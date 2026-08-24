import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentRecommendation:
    """Represents a recommendation from an agent."""
    agent_name: str
    recommendation: Any
    confidence_score: float
    reasoning: str
    metadata: Dict[str, Any] | None = None


class AgentConsensusBuilder:
    """Builds consensus from multiple agent recommendations using voting and confidence weighting."""

    def __init__(self) -> None:
        """Initializes the consensus builder."""
        self._voting_strategy = "confidence_weighted"  # or "majority", "unanimous"

    def build_consensus(
        self,
        recommendations: List[AgentRecommendation],
        strategy: str = "confidence_weighted",
        min_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """Builds consensus from multiple agent recommendations."""
        if not recommendations:
            return {
                "consensus_reached": False,
                "final_recommendation": None,
                "confidence_score": 0.0,
                "reasoning": "No recommendations provided",
                "participating_agents": [],
            }

        # Filter by minimum confidence
        valid_recs = [r for r in recommendations if r.confidence_score >= min_confidence]
        if not valid_recs:
            return {
                "consensus_reached": False,
                "final_recommendation": None,
                "confidence_score": 0.0,
                "reasoning": f"No recommendations met minimum confidence threshold ({min_confidence})",
                "participating_agents": [r.agent_name for r in recommendations],
            }

        if strategy == "confidence_weighted":
            return self._confidence_weighted_consensus(valid_recs)
        elif strategy == "majority":
            return self._majority_voting_consensus(valid_recs)
        elif strategy == "unanimous":
            return self._unanimous_consensus(valid_recs)
        else:
            logger.warning(f"Unknown consensus strategy: {strategy}, falling back to confidence_weighted")
            return self._confidence_weighted_consensus(valid_recs)

    def _confidence_weighted_consensus(
        self,
        recommendations: List[AgentRecommendation],
    ) -> Dict[str, Any]:
        """Selects recommendation with highest confidence score."""
        sorted_recs = sorted(
            recommendations,
            key=lambda r: r.confidence_score,
            reverse=True,
        )
        best_rec = sorted_recs[0]

        # Calculate agreement level
        similar_recs = [
            r for r in recommendations
            if self._are_recommendations_similar(r.recommendation, best_rec.recommendation)
        ]
        agreement_percentage = (len(similar_recs) / len(recommendations)) * 100

        return {
            "consensus_reached": True,
            "final_recommendation": best_rec.recommendation,
            "confidence_score": best_rec.confidence_score,
            "reasoning": best_rec.reasoning,
            "selected_agent": best_rec.agent_name,
            "agreement_percentage": round(agreement_percentage, 1),
            "participating_agents": [r.agent_name for r in recommendations],
            "consensus_strategy": "confidence_weighted",
            "all_recommendations": [
                {
                    "agent": r.agent_name,
                    "confidence": r.confidence_score,
                    "recommendation": str(r.recommendation)[:100],
                }
                for r in sorted_recs
            ],
        }

    def _majority_voting_consensus(
        self,
        recommendations: List[AgentRecommendation],
    ) -> Dict[str, Any]:
        """Selects recommendation that appears most frequently."""
        # Group by similar recommendations
        groups: Dict[str, List[AgentRecommendation]] = {}
        for rec in recommendations:
            key = str(rec.recommendation)
            if key not in groups:
                groups[key] = []
            groups[key].append(rec)

        # Find largest group
        largest_group = max(groups.values(), key=len)
        majority_threshold = len(recommendations) / 2

        if len(largest_group) > majority_threshold:
            # Average confidence across majority
            avg_confidence = sum(r.confidence_score for r in largest_group) / len(largest_group)
            best_rec = max(largest_group, key=lambda r: r.confidence_score)

            return {
                "consensus_reached": True,
                "final_recommendation": best_rec.recommendation,
                "confidence_score": avg_confidence,
                "reasoning": f"Majority vote from {len(largest_group)} agents: {best_rec.reasoning}",
                "selected_agent": f"{len(largest_group)} agents in agreement",
                "agreement_percentage": round((len(largest_group) / len(recommendations)) * 100, 1),
                "participating_agents": [r.agent_name for r in recommendations],
                "consensus_strategy": "majority",
            }
        else:
            # No majority, fall back to highest confidence
            best_rec = max(recommendations, key=lambda r: r.confidence_score)
            return {
                "consensus_reached": False,
                "final_recommendation": best_rec.recommendation,
                "confidence_score": best_rec.confidence_score,
                "reasoning": f"No majority reached, selected highest confidence: {best_rec.reasoning}",
                "selected_agent": best_rec.agent_name,
                "agreement_percentage": round((1 / len(recommendations)) * 100, 1),
                "participating_agents": [r.agent_name for r in recommendations],
                "consensus_strategy": "majority_fallback",
            }

    def _unanimous_consensus(
        self,
        recommendations: List[AgentRecommendation],
    ) -> Dict[str, Any]:
        """Requires all agents to agree on the same recommendation."""
        first_rec = recommendations[0]
        all_agree = all(
            self._are_recommendations_similar(r.recommendation, first_rec.recommendation)
            for r in recommendations
        )

        if all_agree:
            avg_confidence = sum(r.confidence_score for r in recommendations) / len(recommendations)
            return {
                "consensus_reached": True,
                "final_recommendation": first_rec.recommendation,
                "confidence_score": avg_confidence,
                "reasoning": f"Unanimous agreement: {first_rec.reasoning}",
                "selected_agent": "all_agents",
                "agreement_percentage": 100.0,
                "participating_agents": [r.agent_name for r in recommendations],
                "consensus_strategy": "unanimous",
            }
        else:
            return {
                "consensus_reached": False,
                "final_recommendation": None,
                "confidence_score": 0.0,
                "reasoning": "Agents did not reach unanimous agreement",
                "participating_agents": [r.agent_name for r in recommendations],
                "consensus_strategy": "unanimous",
                "conflicting_recommendations": [
                    {
                        "agent": r.agent_name,
                        "recommendation": str(r.recommendation)[:100],
                        "confidence": r.confidence_score,
                    }
                    for r in recommendations
                ],
            }

    def _are_recommendations_similar(
        self,
        rec1: Any,
        rec2: Any,
        threshold: float = 0.8,
    ) -> bool:
        """Checks if two recommendations are similar enough to be considered the same."""
        # For strings, use simple equality
        if isinstance(rec1, str) and isinstance(rec2, str):
            return rec1.lower().strip() == rec2.lower().strip()

        # For numeric values (like discount percentages), check if within threshold
        if isinstance(rec1, (int, float)) and isinstance(rec2, (int, float)):
            return abs(rec1 - rec2) / max(abs(rec1), abs(rec2), 1) < (1 - threshold)

        # For other types, use exact equality
        return rec1 == rec2


# Global singleton instance
agent_consensus_builder = AgentConsensusBuilder()
