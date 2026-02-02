"""
Orchestrator for Multi-Agent System

Main entry point for the multi-agent B2B Account Intelligence system.
Coordinates:
- Query routing via QueryRouter
- Agent execution via AgentExecutor
- Response synthesis via ResponseSynthesizer

The Orchestrator manages the full lifecycle of a query from intake
to final response delivery.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .guardrails.tool_access import AgentType
from .specialists.base_specialist import AgentResponse, AgentStatus
from .router import QueryRouter, RoutingDecision, SynthesisStrategy
from .executor import AgentExecutor, ExecutionMode
from .synthesizer import ResponseSynthesizer, SynthesizedResponse


@dataclass
class OrchestratorResponse:
    """
    Final response from the orchestrator.

    Attributes:
        query: Original query
        answer: Final synthesized answer
        mode: "single_agent" or "multi_agent"
        agents_used: List of agents that contributed
        synthesis_strategy: Strategy used to combine responses
        confidence: Overall confidence score
        latency_ms: Total processing time
        routing_reasoning: Explanation of routing decision
        agent_responses: Individual responses from each agent
        error_message: Error details if applicable
    """
    query: str
    answer: str
    mode: str
    agents_used: List[AgentType]
    synthesis_strategy: SynthesisStrategy
    confidence: float
    latency_ms: float
    routing_reasoning: str
    agent_responses: List[AgentResponse] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "answer": self.answer,
            "mode": self.mode,
            "agents_used": [a.value for a in self.agents_used],
            "synthesis_strategy": self.synthesis_strategy.value,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "routing_reasoning": self.routing_reasoning,
            "agent_responses": [r.to_dict() for r in self.agent_responses],
            "error_message": self.error_message,
        }


class Orchestrator:
    """
    Main orchestrator for the multi-agent system.

    Coordinates the full query processing pipeline:
    1. Query classification and routing
    2. Agent execution (parallel/sequential/hybrid)
    3. Response synthesis
    4. Final response delivery

    The orchestrator is the single entry point for client code.
    """

    def __init__(
        self,
        router: Optional[QueryRouter] = None,
        executor: Optional[AgentExecutor] = None,
        synthesizer: Optional[ResponseSynthesizer] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            router: Query router instance (creates default if not provided)
            executor: Agent executor instance (creates default if not provided)
            synthesizer: Response synthesizer instance (creates default if not provided)
        """
        self.router = router or QueryRouter()
        self.executor = executor or AgentExecutor()
        self.synthesizer = synthesizer or ResponseSynthesizer()

        # Agent registry
        self.agents: Dict[AgentType, Any] = {}

    def register_agent(self, agent_type: AgentType, agent: Any) -> None:
        """
        Register a specialist agent.

        Args:
            agent_type: Type of agent
            agent: Agent instance
        """
        self.agents[agent_type] = agent

    def get_available_agents(self) -> List[AgentType]:
        """
        Get list of available agent types.

        Returns:
            List of registered AgentType values
        """
        return list(self.agents.keys())

    async def execute(self, query: str) -> OrchestratorResponse:
        """
        Execute a query through the multi-agent system.

        Args:
            query: User's query string

        Returns:
            OrchestratorResponse with final answer
        """
        start_time = time.time()

        try:
            # Step 1: Route the query
            routing_decision = await self._route_query(query)

            # Step 2: Execute agents
            agent_responses = await self._execute_agents(routing_decision)

            # Step 3: Synthesize responses
            synthesized = await self._synthesize_responses(
                agent_responses, routing_decision.synthesis_strategy
            )

            latency_ms = (time.time() - start_time) * 1000

            return OrchestratorResponse(
                query=query,
                answer=synthesized.answer,
                mode=routing_decision.mode,
                agents_used=routing_decision.agents,
                synthesis_strategy=routing_decision.synthesis_strategy,
                confidence=synthesized.confidence,
                latency_ms=latency_ms,
                routing_reasoning=routing_decision.reasoning,
                agent_responses=agent_responses,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return self._create_error_response(query, str(e), latency_ms)

    async def _route_query(self, query: str) -> RoutingDecision:
        """
        Route query to appropriate agents.

        Args:
            query: User's query

        Returns:
            RoutingDecision from router

        Raises:
            Exception: If routing fails (will be caught by execute)
        """
        try:
            return await self.router.route(query)
        except Exception as e:
            # Fallback to general agent on routing failure
            return RoutingDecision(
                mode="single_agent",
                agents=[AgentType.GENERAL_FALLBACK],
                subtasks=[{"agent": AgentType.GENERAL_FALLBACK, "query": query}],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=0.5,
                reasoning=f"Routing failed ({str(e)}), using fallback agent.",
            )

    async def _execute_agents(
        self, routing_decision: RoutingDecision
    ) -> List[AgentResponse]:
        """
        Execute agents based on routing decision.

        Args:
            routing_decision: Decision from router

        Returns:
            List of AgentResponse from executed agents

        Raises:
            Exception: If execution fails
        """
        try:
            return await self.executor.execute_agents(
                routing_decision=routing_decision,
                agents=self.agents,
                mode=ExecutionMode.HYBRID,
            )
        except Exception as e:
            # Return error response for all requested agents
            return [
                AgentResponse(
                    agent_type=agent_type,
                    query=routing_decision.subtasks[0]["query"] if routing_decision.subtasks else "",
                    answer=f"Execution failed: {str(e)}",
                    status=AgentStatus.FAILED,
                    confidence=0.0,
                    error_message=str(e),
                    latency_ms=0,
                )
                for agent_type in routing_decision.agents
            ]

    async def _synthesize_responses(
        self,
        responses: List[AgentResponse],
        strategy: SynthesisStrategy,
    ) -> SynthesizedResponse:
        """
        Synthesize agent responses.

        Args:
            responses: Responses from agents
            strategy: Synthesis strategy

        Returns:
            SynthesizedResponse with combined answer
        """
        try:
            return await self.synthesizer.synthesize(responses, strategy)
        except Exception as e:
            # Return best single response if synthesis fails
            successful = [r for r in responses if r.status == AgentStatus.SUCCESS]
            if successful:
                best = max(successful, key=lambda r: r.confidence)
                return SynthesizedResponse(
                    answer=best.answer,
                    confidence=best.confidence * 0.8,  # Reduce confidence due to synthesis failure
                    sources=best.sources,
                    agent_contributions={best.agent_type.value: best.answer},
                    synthesis_strategy=strategy,
                    latency_ms=best.latency_ms,
                )
            else:
                return SynthesizedResponse(
                    answer=f"Failed to process query: {str(e)}",
                    confidence=0.0,
                    sources=[],
                    agent_contributions={},
                    synthesis_strategy=strategy,
                    latency_ms=0,
                )

    def _create_error_response(
        self, query: str, error_message: str, latency_ms: float
    ) -> OrchestratorResponse:
        """
        Create error response.

        Args:
            query: Original query
            error_message: Error description
            latency_ms: Time elapsed

        Returns:
            OrchestratorResponse with error
        """
        return OrchestratorResponse(
            query=query,
            answer=f"An error occurred while processing your query: {error_message}",
            mode="error",
            agents_used=[],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.0,
            latency_ms=latency_ms,
            routing_reasoning="Error occurred during processing.",
            error_message=error_message,
        )

    async def execute_with_context(
        self,
        query: str,
        conversation_history: List[Dict[str, str]],
    ) -> OrchestratorResponse:
        """
        Execute query with conversation context.

        Args:
            query: Current query
            conversation_history: Previous messages

        Returns:
            OrchestratorResponse with answer
        """
        # For now, just execute the query
        # Future: Pass context to agents
        return await self.execute(query)

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.

        Returns:
            Dict with system info
        """
        return {
            "available_agents": [a.value for a in self.agents.keys()],
            "total_agents": len(self.agents),
            "router_model": self.router.model,
            "synthesizer_model": self.synthesizer.model,
            "status": "ready" if self.agents else "no_agents",
        }
