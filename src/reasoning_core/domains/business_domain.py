"""Business domain plugin for reasoning extraction.

Implements business reasoning patterns including:
- Sales processes
- Objection handling
- Value proposition mapping
- Strategic frameworks
"""

from typing import List, Dict, Any
from reasoning_core.domains.base_domain import (
    BaseDomain,
    Concept,
    Relationship,
    ReasoningPattern
)


class BusinessDomain(BaseDomain):
    """Business training domain implementation."""
    
    def get_domain_name(self) -> str:
        return "business"
    
    def get_terminology_mapping(self) -> Dict[str, List[str]]:
        """Business terminology categories."""
        return {
            "strategy": [
                "upselling", "cross-selling", "objection handling",
                "value proposition", "positioning", "competitive advantage"
            ],
            "metric": [
                "conversion rate", "LTV", "CAC", "churn rate", "ARR", "MRR",
                "pipeline", "quota", "win rate"
            ],
            "framework": [
                "MEDDIC", "BANT", "SPIN", "Challenger", "solution selling",
                "consultative selling"
            ],
            "stage": [
                "prospecting", "qualification", "discovery", "proposal",
                "negotiation", "closing"
            ],
            "pain_point": [
                "cost", "efficiency", "scalability", "risk", "compliance",
                "time to market"
            ],
            "value": [
                "ROI", "cost savings", "revenue increase", "risk reduction",
                "efficiency gain"
            ],
        }
    
    def get_reasoning_patterns(self) -> List[ReasoningPattern]:
        """Business reasoning patterns."""
        return [
            ReasoningPattern(
                name="sales_process",
                description="Lead to close workflow",
                steps=[
                    "Identify prospect",
                    "Qualify (BANT/MEDDIC)",
                    "Discovery call",
                    "Present solution",
                    "Handle objections",
                    "Close deal"
                ],
                example="Inbound lead → Budget confirmed → Pain identified → Demo scheduled → Price objection → ROI shown → Deal closed"
            ),
            ReasoningPattern(
                name="value_mapping",
                description="Feature to benefit to value",
                steps=[
                    "Product feature",
                    "Functional benefit",
                    "Business value",
                    "Quantified ROI"
                ],
                example="Automation feature → Saves time → Reduces labor cost → $50k annual savings"
            ),
            ReasoningPattern(
                name="objection_handling",
                description="Objection to response",
                steps=[
                    "Identify objection",
                    "Acknowledge concern",
                    "Provide evidence",
                    "Confirm resolution"
                ],
                example="'Too expensive' → 'I understand' → Show ROI calculation → 'Does this address your concern?'"
            ),
            ReasoningPattern(
                name="competitive_positioning",
                description="Differentiation strategy",
                steps=[
                    "Identify competitor",
                    "Note their strengths",
                    "Highlight differentiators",
                    "Emphasize unique value"
                ],
                example="Competitor A → Good price → But we have better support → 24/7 availability saves downtime"
            ),
        ]
    
    def extract_concepts(self, text: str) -> List[Concept]:
        """Extract business concepts from text.
        
        TODO: Implement with NER or LLM
        """
        concepts = []
        text_lower = text.lower()
        
        for concept_type, terms in self.terminology.items():
            for term in terms:
                if term.lower() in text_lower:
                    idx = text_lower.index(term.lower())
                    start = max(0, idx - 50)
                    end = min(len(text), idx + len(term) + 50)
                    context = text[start:end]
                    
                    concepts.append(Concept(
                        name=term,
                        type=concept_type,
                        context=context,
                        confidence=0.8,
                        metadata={"domain": "business"}
                    ))
        
        return concepts
    
    def identify_relationships(self, concepts: List[Concept]) -> List[Relationship]:
        """Identify business relationships.
        
        TODO: Implement with LLM
        """
        relationships = []
        
        rules = {
            ("pain_point", "value"): "addressed_by",
            ("strategy", "stage"): "used_in",
            ("framework", "stage"): "applies_to",
            ("metric", "value"): "measures",
        }
        
        for i, source in enumerate(concepts):
            for target in concepts[i+1:]:
                rule_key = (source.type, target.type)
                if rule_key in rules:
                    relationships.append(Relationship(
                        source=source,
                        target=target,
                        relationship_type=rules[rule_key],
                        strength=0.7,
                        metadata={"domain": "business"}
                    ))
        
        return relationships
    
    def build_reasoning_chains(
        self,
        concepts: List[Concept],
        relationships: List[Relationship]
    ) -> List[Dict[str, Any]]:
        """Build business reasoning chains.
        
        TODO: Implement pattern matching
        """
        return []
    
    def generate_questions(
        self,
        concepts: List[Concept],
        chains: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate business training questions.
        
        TODO: Implement with LLM
        """
        questions = []
        
        strategies = [c for c in concepts if c.type == "strategy"]
        for strategy in strategies[:3]:
            questions.append(f"When should you use {strategy.name}?")
            questions.append(f"What are best practices for {strategy.name}?")
        
        return questions
