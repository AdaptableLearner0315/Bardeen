"""
Agent Utilization Metrics for Multi-Agent System Evaluation

Tracks how agents are being utilized:
- Usage frequency per agent
- Average execution time per agent
- Success/failure rates per agent
- Multi-agent collaboration patterns
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from collections import defaultdict

from ..guardrails.tool_access import AgentType
from ..specialists.base_specialist import AgentStatus


@dataclass
class AgentUtilizationResult:
    """Utilization metrics for a single agent."""
    agent_type: AgentType
    total_invocations: int
    successful_invocations: int
    failed_invocations: int
    timeout_invocations: int
    total_latency_ms: float
    avg_latency_ms: float
    success_rate: float


@dataclass
class UtilizationMetrics:
    """
    Metrics for tracking agent utilization patterns.

    Tracks:
    - Invocation counts per agent
    - Success/failure rates
    - Latency statistics
    - Multi-agent collaboration frequency
    """

    agent_stats: Dict[AgentType, Dict[str, any]] = field(
        default_factory=lambda: defaultdict(
            lambda: {
                "invocations": 0,
                "successes": 0,
                "failures": 0,
                "timeouts": 0,
                "total_latency_ms": 0.0,
            }
        )
    )
    multi_agent_queries: int = 0
    single_agent_queries: int = 0
    collaboration_patterns: Dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    total_queries: int = 0

    def record_agent_invocation(
        self,
        agent_type: AgentType,
        status: AgentStatus,
        latency_ms: float,
    ) -> None:
        """
        Record an agent invocation.

        Args:
            agent_type: Type of agent invoked
            status: Result status of the invocation
            latency_ms: Execution latency in milliseconds
        """
        stats = self.agent_stats[agent_type]
        stats["invocations"] += 1
        stats["total_latency_ms"] += latency_ms

        if status == AgentStatus.SUCCESS:
            stats["successes"] += 1
        elif status == AgentStatus.FAILED:
            stats["failures"] += 1
        elif status == AgentStatus.TIMEOUT:
            stats["timeouts"] += 1

    def record_query_routing(
        self,
        agents_used: List[AgentType],
    ) -> None:
        """
        Record which agents were used for a query.

        Args:
            agents_used: List of agents used for the query
        """
        self.total_queries += 1

        if len(agents_used) > 1:
            self.multi_agent_queries += 1
            # Record collaboration pattern
            pattern = "+".join(sorted(a.value for a in agents_used))
            self.collaboration_patterns[pattern] += 1
        else:
            self.single_agent_queries += 1

    def get_agent_utilization(self, agent_type: AgentType) -> AgentUtilizationResult:
        """
        Get utilization metrics for a specific agent.

        Args:
            agent_type: Agent type to get metrics for

        Returns:
            AgentUtilizationResult with detailed metrics
        """
        stats = self.agent_stats.get(agent_type)
        if not stats or stats["invocations"] == 0:
            return AgentUtilizationResult(
                agent_type=agent_type,
                total_invocations=0,
                successful_invocations=0,
                failed_invocations=0,
                timeout_invocations=0,
                total_latency_ms=0.0,
                avg_latency_ms=0.0,
                success_rate=0.0,
            )

        total = stats["invocations"]
        successes = stats["successes"]
        total_latency = stats["total_latency_ms"]

        return AgentUtilizationResult(
            agent_type=agent_type,
            total_invocations=total,
            successful_invocations=successes,
            failed_invocations=stats["failures"],
            timeout_invocations=stats["timeouts"],
            total_latency_ms=total_latency,
            avg_latency_ms=total_latency / total if total > 0 else 0.0,
            success_rate=successes / total if total > 0 else 0.0,
        )

    @property
    def multi_agent_rate(self) -> float:
        """Percentage of queries using multiple agents."""
        if self.total_queries == 0:
            return 0.0
        return self.multi_agent_queries / self.total_queries

    @property
    def overall_success_rate(self) -> float:
        """Overall success rate across all agents."""
        total_invocations = sum(
            stats["invocations"] for stats in self.agent_stats.values()
        )
        total_successes = sum(
            stats["successes"] for stats in self.agent_stats.values()
        )
        if total_invocations == 0:
            return 0.0
        return total_successes / total_invocations

    @property
    def average_latency_ms(self) -> float:
        """Average latency across all agent invocations."""
        total_invocations = sum(
            stats["invocations"] for stats in self.agent_stats.values()
        )
        total_latency = sum(
            stats["total_latency_ms"] for stats in self.agent_stats.values()
        )
        if total_invocations == 0:
            return 0.0
        return total_latency / total_invocations

    def get_most_used_agents(self, top_n: int = 5) -> List[AgentUtilizationResult]:
        """Get the most frequently used agents."""
        agent_results = [
            self.get_agent_utilization(agent_type)
            for agent_type in AgentType
            if agent_type != AgentType.ORCHESTRATOR
        ]
        sorted_results = sorted(
            agent_results, key=lambda x: x.total_invocations, reverse=True
        )
        return sorted_results[:top_n]

    def get_collaboration_patterns(
        self, top_n: int = 5
    ) -> List[tuple[str, int]]:
        """Get most common multi-agent collaboration patterns."""
        sorted_patterns = sorted(
            self.collaboration_patterns.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_patterns[:top_n]

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "total_queries": self.total_queries,
            "multi_agent_queries": self.multi_agent_queries,
            "single_agent_queries": self.single_agent_queries,
            "multi_agent_rate": self.multi_agent_rate,
            "overall_success_rate": self.overall_success_rate,
            "average_latency_ms": self.average_latency_ms,
            "agent_utilization": {
                agent_type.value: {
                    "total_invocations": self.get_agent_utilization(agent_type).total_invocations,
                    "success_rate": self.get_agent_utilization(agent_type).success_rate,
                    "avg_latency_ms": self.get_agent_utilization(agent_type).avg_latency_ms,
                }
                for agent_type in AgentType
                if agent_type != AgentType.ORCHESTRATOR
                and self.get_agent_utilization(agent_type).total_invocations > 0
            },
            "collaboration_patterns": dict(
                self.get_collaboration_patterns(top_n=10)
            ),
        }
