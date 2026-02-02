"""
Multi-Agent API Integration

Provides integration between the multi-agent system and the FastAPI backend.
Includes:
- Multi-agent chat endpoint handler
- Input/output validation integration
- Graceful degradation to single agent
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .orchestrator import Orchestrator
from .router import RoutingDecision
from .synthesizer import SynthesizedResponse
from .guardrails.input_validator import InputValidator, ValidationResult
from .guardrails.output_validator import OutputValidator
from .guardrails.tool_access import AgentType
from .specialists.base_specialist import AgentResponse, AgentStatus


@dataclass
class MultiAgentChatResponse:
    """Response from multi-agent chat endpoint."""
    answer: str
    mode: str  # "single_agent" or "multi_agent"
    agents_used: List[str]
    routing_decision: Dict[str, Any]
    agent_contributions: Dict[str, str]
    sources: List[str]
    confidence: float
    latency_ms: float
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "answer": self.answer,
            "mode": self.mode,
            "agents_used": self.agents_used,
            "routing_decision": self.routing_decision,
            "agent_contributions": self.agent_contributions,
            "sources": self.sources,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "warnings": self.warnings,
            "error_message": self.error_message,
        }


class MultiAgentAPIHandler:
    """
    Handles multi-agent API requests.

    Integrates:
    - Input validation
    - Query routing
    - Agent execution
    - Response synthesis
    - Output validation
    """

    def __init__(
        self,
        orchestrator: Optional[Orchestrator] = None,
        enable_validation: bool = True,
    ):
        """
        Initialize the API handler.

        Args:
            orchestrator: Optional pre-configured orchestrator
            enable_validation: Whether to enable input/output validation
        """
        self.orchestrator = orchestrator
        self.enable_validation = enable_validation
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the orchestrator and agents."""
        if not self.orchestrator:
            self.orchestrator = Orchestrator()
            await self.orchestrator.initialize()
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        """Check if handler is initialized."""
        return self._initialized and self.orchestrator is not None

    async def process_query(
        self,
        query: str,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> MultiAgentChatResponse:
        """
        Process a user query through the multi-agent system.

        Args:
            query: User's query string
            context: Optional conversation context

        Returns:
            MultiAgentChatResponse with answer and metadata
        """
        start_time = time.time()
        warnings: List[str] = []

        # Step 1: Validate input
        if self.enable_validation:
            validation_result = InputValidator.validate(query)

            if not validation_result.is_valid:
                return MultiAgentChatResponse(
                    answer=f"Invalid query: {validation_result.error_message}",
                    mode="error",
                    agents_used=[],
                    routing_decision={},
                    agent_contributions={},
                    sources=[],
                    confidence=0.0,
                    latency_ms=self._calculate_latency(start_time),
                    error_message=validation_result.error_message,
                )

            # Use sanitized query and collect warnings
            query = validation_result.sanitized_input
            warnings.extend(validation_result.warnings)

        # Step 2: Check initialization
        if not self.is_initialized:
            try:
                await self.initialize()
            except Exception as e:
                return MultiAgentChatResponse(
                    answer="System not available. Please try again later.",
                    mode="error",
                    agents_used=[],
                    routing_decision={},
                    agent_contributions={},
                    sources=[],
                    confidence=0.0,
                    latency_ms=self._calculate_latency(start_time),
                    error_message=f"Initialization failed: {str(e)}",
                )

        # Step 3: Process through orchestrator
        try:
            response = await self.orchestrator.process(query, context)

            # Step 4: Validate output
            if self.enable_validation and response.agent_responses:
                for agent_response in response.agent_responses:
                    output_validation = OutputValidator.validate(agent_response)
                    if output_validation.confidence_warning:
                        warnings.append(output_validation.message)

            # Build response
            return MultiAgentChatResponse(
                answer=response.synthesized.answer if response.synthesized else response.final_answer,
                mode=response.routing_decision.mode,
                agents_used=[a.value for a in response.routing_decision.agents],
                routing_decision=response.routing_decision.to_dict(),
                agent_contributions=response.synthesized.agent_contributions if response.synthesized else {},
                sources=response.synthesized.sources if response.synthesized else [],
                confidence=response.synthesized.confidence if response.synthesized else response.routing_decision.confidence,
                latency_ms=self._calculate_latency(start_time),
                warnings=warnings,
            )

        except Exception as e:
            # Graceful degradation
            return MultiAgentChatResponse(
                answer=f"I encountered an error processing your request. Please try again.",
                mode="error",
                agents_used=[],
                routing_decision={},
                agent_contributions={},
                sources=[],
                confidence=0.0,
                latency_ms=self._calculate_latency(start_time),
                warnings=warnings,
                error_message=str(e),
            )

    def _calculate_latency(self, start_time: float) -> float:
        """Calculate latency in milliseconds."""
        return (time.time() - start_time) * 1000

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the multi-agent system."""
        return {
            "initialized": self.is_initialized,
            "orchestrator_ready": self.orchestrator is not None,
            "validation_enabled": self.enable_validation,
            "available_agents": [
                AgentType.COMPANY_RESEARCH.value,
                AgentType.FINANCIAL_ANALYST.value,
                AgentType.COMPETITIVE_INTEL.value,
                AgentType.ACTION_EXECUTOR.value,
                AgentType.GENERAL_FALLBACK.value,
            ],
        }


# Singleton instance for FastAPI integration
_api_handler: Optional[MultiAgentAPIHandler] = None


async def get_multi_agent_handler() -> MultiAgentAPIHandler:
    """Get or create the multi-agent API handler singleton."""
    global _api_handler
    if _api_handler is None:
        _api_handler = MultiAgentAPIHandler()
    return _api_handler
