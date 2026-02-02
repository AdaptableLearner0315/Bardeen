"""
Agent Executor for Multi-Agent System

Executes specialist agents based on routing decisions.
Supports:
- Parallel execution for independent tasks
- Sequential execution for dependent tasks
- Hybrid mode that analyzes dependencies
- Error handling with graceful degradation
- Timeout management
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from .guardrails.tool_access import AgentType
from .specialists.base_specialist import AgentResponse, AgentStatus
from .router import RoutingDecision, SynthesisStrategy


class ExecutionMode(Enum):
    """Mode of agent execution."""
    PARALLEL = "parallel"     # Run all agents simultaneously
    SEQUENTIAL = "sequential"  # Run agents one after another
    HYBRID = "hybrid"          # Analyze dependencies and optimize


@dataclass
class ExecutionPlan:
    """Plan for executing agents."""
    parallel_groups: List[List[AgentType]]
    has_dependencies: bool
    dependency_chain: List[AgentType]


class AgentExecutor:
    """
    Executes agents based on routing decisions.

    Handles:
    - Parallel execution for independent tasks
    - Sequential execution when outputs feed into each other
    - Hybrid mode that analyzes the query to determine optimal execution
    - Graceful degradation when agents fail
    - Timeout management for slow agents
    """

    # Default timeout for agent execution
    DEFAULT_TIMEOUT_SECONDS = 30.0

    def __init__(self, timeout_seconds: Optional[float] = None):
        """
        Initialize the executor.

        Args:
            timeout_seconds: Default timeout for agent execution
        """
        self.timeout_seconds = timeout_seconds or self.DEFAULT_TIMEOUT_SECONDS

    async def execute_agents(
        self,
        routing_decision: RoutingDecision,
        agents: Dict[AgentType, Any],
        mode: ExecutionMode = ExecutionMode.HYBRID,
        timeout_seconds: Optional[float] = None,
    ) -> List[AgentResponse]:
        """
        Execute agents based on routing decision.

        Args:
            routing_decision: Decision from QueryRouter
            agents: Dictionary mapping AgentType to agent instances
            mode: Execution mode (parallel, sequential, hybrid)
            timeout_seconds: Override default timeout

        Returns:
            List of AgentResponse from each agent
        """
        timeout = timeout_seconds or self.timeout_seconds

        # Determine execution mode
        if mode == ExecutionMode.HYBRID:
            plan = self._analyze_dependencies(routing_decision)
            if plan.has_dependencies:
                mode = ExecutionMode.SEQUENTIAL
            else:
                mode = ExecutionMode.PARALLEL

        if mode == ExecutionMode.PARALLEL:
            return await self._execute_parallel(
                routing_decision, agents, timeout
            )
        else:
            return await self._execute_sequential(
                routing_decision, agents, timeout
            )

    async def _execute_parallel(
        self,
        routing_decision: RoutingDecision,
        agents: Dict[AgentType, Any],
        timeout: float,
    ) -> List[AgentResponse]:
        """
        Execute agents in parallel.

        Args:
            routing_decision: Routing decision with subtasks
            agents: Available agents
            timeout: Timeout in seconds

        Returns:
            List of responses from all agents
        """
        tasks = []
        subtask_agent_pairs = []

        for subtask in routing_decision.subtasks:
            agent_type = subtask["agent"]
            query = subtask["query"]

            if agent_type in agents:
                agent = agents[agent_type]
                task = self._execute_with_timeout(
                    agent, query, None, timeout, agent_type
                )
                tasks.append(task)
                subtask_agent_pairs.append((agent_type, query))
            else:
                # Agent not available - create error response
                tasks.append(self._create_missing_agent_response(agent_type, query))
                subtask_agent_pairs.append((agent_type, query))

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        responses = []
        for idx, result in enumerate(results):
            agent_type, query = subtask_agent_pairs[idx]

            if isinstance(result, Exception):
                responses.append(AgentResponse(
                    agent_type=agent_type,
                    query=query,
                    answer=f"Agent failed: {str(result)}",
                    status=AgentStatus.FAILED,
                    confidence=0.0,
                    error_message=str(result),
                    latency_ms=0,
                ))
            else:
                responses.append(result)

        return responses

    async def _execute_sequential(
        self,
        routing_decision: RoutingDecision,
        agents: Dict[AgentType, Any],
        timeout: float,
    ) -> List[AgentResponse]:
        """
        Execute agents sequentially, passing context between them.

        Args:
            routing_decision: Routing decision with subtasks
            agents: Available agents
            timeout: Timeout in seconds

        Returns:
            List of responses from all agents in order
        """
        responses = []
        previous_context = None

        for subtask in routing_decision.subtasks:
            agent_type = subtask["agent"]
            query = subtask["query"]

            if agent_type not in agents:
                response = await self._create_missing_agent_response(agent_type, query)
                responses.append(response)
                continue

            agent = agents[agent_type]

            # Build context from previous responses
            context_messages = None
            if previous_context:
                context_messages = [
                    {
                        "role": "assistant",
                        "content": f"Previous agent ({previous_context['agent']}) said: {previous_context['answer']}"
                    }
                ]

            response = await self._execute_with_timeout(
                agent, query, context_messages, timeout, agent_type
            )
            responses.append(response)

            # Update context for next agent
            if response.status == AgentStatus.SUCCESS:
                previous_context = {
                    "agent": agent_type.value,
                    "answer": response.answer,
                }

        return responses

    async def _execute_with_timeout(
        self,
        agent: Any,
        query: str,
        context: Optional[List[Dict[str, Any]]],
        timeout: float,
        agent_type: AgentType,
    ) -> AgentResponse:
        """
        Execute an agent with timeout handling.

        Args:
            agent: Agent instance to execute
            query: Query to process
            context: Optional context messages
            timeout: Timeout in seconds
            agent_type: Type of agent for error responses

        Returns:
            AgentResponse (success, timeout, or error)
        """
        try:
            # Create execution task
            task = asyncio.create_task(agent.execute(query, context))

            # Wait with timeout
            response = await asyncio.wait_for(task, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            return AgentResponse(
                agent_type=agent_type,
                query=query,
                answer="Request timed out. Please try again.",
                status=AgentStatus.TIMEOUT,
                confidence=0.0,
                error_message=f"Timeout after {timeout}s",
                latency_ms=timeout * 1000,
            )

        except Exception as e:
            return AgentResponse(
                agent_type=agent_type,
                query=query,
                answer=f"Agent execution failed: {str(e)}",
                status=AgentStatus.FAILED,
                confidence=0.0,
                error_message=str(e),
                latency_ms=0,
            )

    async def _create_missing_agent_response(
        self, agent_type: AgentType, query: str
    ) -> AgentResponse:
        """
        Create error response for missing agent.

        Args:
            agent_type: Type of missing agent
            query: Original query

        Returns:
            AgentResponse with error status
        """
        return AgentResponse(
            agent_type=agent_type,
            query=query,
            answer=f"Agent '{agent_type.value}' is not available.",
            status=AgentStatus.FAILED,
            confidence=0.0,
            error_message=f"Agent {agent_type.value} not available in system.",
            latency_ms=0,
        )

    def _analyze_dependencies(
        self, routing_decision: RoutingDecision
    ) -> ExecutionPlan:
        """
        Analyze dependencies between agents in a routing decision.

        Args:
            routing_decision: Routing decision to analyze

        Returns:
            ExecutionPlan with dependency information
        """
        agents = routing_decision.agents
        strategy = routing_decision.synthesis_strategy

        # Sequential strategy indicates dependencies
        if strategy == SynthesisStrategy.SEQUENTIAL:
            return ExecutionPlan(
                parallel_groups=[],
                has_dependencies=True,
                dependency_chain=agents,
            )

        # Action executor typically depends on other agents
        if AgentType.ACTION_EXECUTOR in agents and len(agents) > 1:
            # Action executor should run last
            other_agents = [a for a in agents if a != AgentType.ACTION_EXECUTOR]
            return ExecutionPlan(
                parallel_groups=[other_agents],
                has_dependencies=True,
                dependency_chain=other_agents + [AgentType.ACTION_EXECUTOR],
            )

        # Research agents can typically run in parallel
        research_agents = [
            AgentType.COMPANY_RESEARCH,
            AgentType.FINANCIAL_ANALYST,
            AgentType.COMPETITIVE_INTEL,
            AgentType.GENERAL_FALLBACK,
        ]

        parallel_agents = [a for a in agents if a in research_agents]

        if len(parallel_agents) == len(agents):
            # All agents are research agents - can run in parallel
            return ExecutionPlan(
                parallel_groups=[parallel_agents],
                has_dependencies=False,
                dependency_chain=[],
            )

        # Mixed case - need sequential
        return ExecutionPlan(
            parallel_groups=[],
            has_dependencies=True,
            dependency_chain=agents,
        )
