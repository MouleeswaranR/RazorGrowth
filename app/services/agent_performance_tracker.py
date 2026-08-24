import time
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformanceMetrics:
    """Tracks performance metrics for an individual agent execution."""
    agent_name: str
    start_time: float
    end_time: float | None = None
    latency_ms: float | None = None
    status: str = "pending"  # pending, success, failed
    error_message: str | None = None
    input_size: int = 0
    output_size: int = 0


@dataclass
class AgentStats:
    """Aggregated statistics for an agent."""
    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0
    executions: List[AgentPerformanceMetrics] = field(default_factory=list)


class AgentPerformanceTracker:
    """Tracks and aggregates performance metrics for all agents in the system."""

    def __init__(self) -> None:
        """Initializes the performance tracker with empty state."""
        self._agent_stats: Dict[str, AgentStats] = {}
        self._current_executions: Dict[str, AgentPerformanceMetrics] = {}

    def start_tracking(
        self,
        agent_name: str,
        execution_id: str | None = None,
        input_size: int = 0,
    ) -> str:
        """Starts tracking an agent execution and returns execution ID."""
        exec_id = execution_id or f"{agent_name}_{int(time.time() * 1000)}"
        
        metrics = AgentPerformanceMetrics(
            agent_name=agent_name,
            start_time=time.time(),
            input_size=input_size,
            status="pending",
        )
        
        self._current_executions[exec_id] = metrics
        return exec_id

    def end_tracking(
        self,
        execution_id: str,
        status: str = "success",
        error_message: str | None = None,
        output_size: int = 0,
    ) -> AgentPerformanceMetrics | None:
        """Ends tracking for an agent execution and records metrics."""
        metrics = self._current_executions.pop(execution_id, None)
        if not metrics:
            logger.warning(f"No tracking found for execution_id: {execution_id}")
            return None

        metrics.end_time = time.time()
        metrics.latency_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.status = status
        metrics.error_message = error_message
        metrics.output_size = output_size

        # Update aggregated stats
        self._update_stats(metrics)

        return metrics

    def _update_stats(self, metrics: AgentPerformanceMetrics) -> None:
        """Updates aggregated statistics for an agent."""
        agent_name = metrics.agent_name
        
        if agent_name not in self._agent_stats:
            self._agent_stats[agent_name] = AgentStats(agent_name=agent_name)

        stats = self._agent_stats[agent_name]
        stats.total_executions += 1
        
        if metrics.status == "success":
            stats.successful_executions += 1
        else:
            stats.failed_executions += 1

        if metrics.latency_ms:
            stats.total_latency_ms += metrics.latency_ms
            stats.min_latency_ms = min(stats.min_latency_ms, metrics.latency_ms)
            stats.max_latency_ms = max(stats.max_latency_ms, metrics.latency_ms)
            stats.avg_latency_ms = stats.total_latency_ms / stats.total_executions

        stats.success_rate = (
            stats.successful_executions / stats.total_executions
        ) if stats.total_executions > 0 else 0.0

        # Keep only last 100 executions per agent
        stats.executions.append(metrics)
        if len(stats.executions) > 100:
            stats.executions.pop(0)

    def get_agent_stats(self, agent_name: str) -> AgentStats | None:
        """Retrieves aggregated statistics for a specific agent."""
        return self._agent_stats.get(agent_name)

    def get_all_stats(self) -> Dict[str, dict]:
        """Retrieves all agent statistics as a dictionary."""
        return {
            name: {
                "agent_name": stats.agent_name,
                "total_executions": stats.total_executions,
                "successful_executions": stats.successful_executions,
                "failed_executions": stats.failed_executions,
                "avg_latency_ms": round(stats.avg_latency_ms, 2),
                "min_latency_ms": round(stats.min_latency_ms, 2) if stats.min_latency_ms != float('inf') else 0.0,
                "max_latency_ms": round(stats.max_latency_ms, 2),
                "success_rate": round(stats.success_rate * 100, 2),
            }
            for name, stats in self._agent_stats.items()
        }

    def get_recent_executions(self, agent_name: str, limit: int = 10) -> List[dict]:
        """Retrieves recent executions for a specific agent."""
        stats = self._agent_stats.get(agent_name)
        if not stats:
            return []

        recent = stats.executions[-limit:]
        return [
            {
                "agent_name": m.agent_name,
                "latency_ms": round(m.latency_ms, 2) if m.latency_ms else 0.0,
                "status": m.status,
                "error_message": m.error_message,
                "input_size": m.input_size,
                "output_size": m.output_size,
                "timestamp": datetime.fromtimestamp(m.start_time).isoformat(),
            }
            for m in recent
        ]

    def reset_stats(self, agent_name: str | None = None) -> None:
        """Resets statistics for a specific agent or all agents."""
        if agent_name:
            self._agent_stats.pop(agent_name, None)
        else:
            self._agent_stats.clear()


# Global singleton instance
agent_performance_tracker = AgentPerformanceTracker()
