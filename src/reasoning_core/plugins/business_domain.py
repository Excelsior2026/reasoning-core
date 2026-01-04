"""Business domain plugin for business reasoning extraction."""

from typing import List, Dict
from reasoning_core.plugins.base_domain import BaseDomain
from reasoning_core.extractors.concept_extractor import Concept
from reasoning_core.extractors.relationship_mapper import Relationship
from reasoning_core.extractors.reasoning_chain_builder import ReasoningChain, ReasoningStep
import re


class BusinessDomain(BaseDomain):
    """Business training and analysis domain."""

    TERMINOLOGY = {
        "strategies": [
            "upselling",
            "cross-selling",
            "objection handling",
            "value proposition",
            "competitive positioning",
            "market penetration",
            "customer retention",
        ],
        "metrics": [
            "conversion rate",
            "LTV",
            "CAC",
            "ROI",
            "churn rate",
            "NPS",
            "revenue",
            "profit margin",
            "market share",
        ],
        "frameworks": ["MEDDIC", "BANT", "SPIN", "Challenger", "SWOT", "Porter's Five Forces"],
        "activities": [
            "prospecting",
            "qualification",
            "discovery",
            "demo",
            "proposal",
            "negotiation",
            "closing",
            "onboarding",
        ],
        "pain_points": [
            "inefficiency",
            "cost",
            "complexity",
            "risk",
            "compliance",
            "scalability",
            "integration",
        ],
    }

    REASONING_PATTERNS = [
        "problem_to_solution",
        "objection_to_response",
        "feature_to_benefit",
        "pain_to_value",
        "competitor_to_differentiation",
    ]

    def get_name(self) -> str:
        """Get domain name."""
        return "business"

    def extract_concepts(self, text: str) -> List[Concept]:
        """Extract business concepts from text."""
        concepts = []
        text_lower = text.lower()

        # Extract concepts by category
        for category, terms in self.TERMINOLOGY.items():
            for term in terms:
                pattern = r"\b" + re.escape(term.lower()) + r"\b"
                for match in re.finditer(pattern, text_lower):
                    concepts.append(
                        Concept(
                            text=term,
                            type=category,
                            confidence=0.85,
                            context=text[max(0, match.start() - 30) : match.end() + 30],
                            position=match.start(),
                        )
                    )

        return concepts

    def identify_relationships(self, concepts: List[Concept], text: str) -> List[Relationship]:
        """Identify business relationships between concepts."""
        relationships = []

        for i, source in enumerate(concepts):
            for target in concepts[i + 1 :]:
                rel_type = self._determine_business_relationship(source, target)
                if rel_type:
                    relationships.append(
                        Relationship(
                            source=source,
                            target=target,
                            type=rel_type,
                            confidence=0.8,
                            evidence=self._extract_evidence(source, target, text),
                        )
                    )

        return relationships

    def _determine_business_relationship(self, source: Concept, target: Concept) -> str:
        """Determine business relationship type."""
        # Pain point → Strategy
        if source.type == "pain_points" and target.type == "strategies":
            return "addressed_by"

        # Strategy → Metric
        if source.type == "strategies" and target.type == "metrics":
            return "measured_by"

        # Framework → Activity
        if source.type == "frameworks" and target.type == "activities":
            return "guides"

        # Activity → Metric
        if source.type == "activities" and target.type == "metrics":
            return "impacts"

        return "relates_to"

    def _extract_evidence(self, source: Concept, target: Concept, text: str) -> str:
        """Extract evidence for relationship."""
        start = min(source.position, target.position)
        end = max(source.position + len(source.text), target.position + len(target.text))
        return text[max(0, start - 20) : min(len(text), end + 20)]

    def build_reasoning_chains(self, concepts: List[Concept], relationships: List[Relationship]) -> List[ReasoningChain]:
        """Build business reasoning chains."""
        chains = []

        # Build sales chain: pain → strategy → activity → outcome
        sales_chain = self._build_sales_chain(concepts, relationships)
        if sales_chain:
            chains.append(sales_chain)

        return chains

    def _build_sales_chain(self, concepts: List[Concept], relationships: List[Relationship]) -> ReasoningChain:
        """Build a sales reasoning chain."""
        steps = []

        # Find pain point
        pains = [c for c in concepts if c.type == "pain_points"]
        if pains:
            steps.append(ReasoningStep(concept=pains[0], action="identify", rationale="Customer pain point"))

        # Find strategy
        strategies = [c for c in concepts if c.type == "strategies"]
        if strategies:
            steps.append(
                ReasoningStep(concept=strategies[0], action="apply", rationale="Strategic approach")
            )

        # Find metric
        metrics = [c for c in concepts if c.type == "metrics"]
        if metrics:
            steps.append(
                ReasoningStep(concept=metrics[0], action="measure", rationale="Track effectiveness")
            )

        if len(steps) >= 2:
            return ReasoningChain(type="sales", steps=steps, confidence=0.75, domain="business")
        return None

    def generate_questions(self, content: Dict) -> List[str]:
        """Generate business questions."""
        questions = []

        if "strategies" in content:
            for strategy in content["strategies"]:
                questions.append(f"When should you use {strategy}?")
                questions.append(f"What metrics indicate success with {strategy}?")

        return questions

    def get_terminology_mapping(self) -> Dict:
        """Get business terminology mapping."""
        return self.TERMINOLOGY

    def get_reasoning_patterns(self) -> List[str]:
        """Get business reasoning patterns."""
        return self.REASONING_PATTERNS
