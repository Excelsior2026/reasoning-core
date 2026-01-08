"""Medical domain plugin for clinical reasoning extraction."""

from typing import List, Dict
from reasoning_core.plugins.base_domain import BaseDomain
from reasoning_core.extractors.concept_extractor import Concept
from reasoning_core.extractors.relationship_mapper import Relationship
from reasoning_core.extractors.reasoning_chain_builder import ReasoningChain, ReasoningStep
from typing import Optional
import re


class MedicalDomain(BaseDomain):
    """Medical education and clinical reasoning domain."""

    TERMINOLOGY = {
        "symptoms": [
            "pain",
            "fever",
            "cough",
            "dyspnea",
            "fatigue",
            "nausea",
            "vomiting",
            "diarrhea",
            "headache",
            "dizziness",
        ],
        "diseases": [
            "myocardial infarction",
            "MI",
            "pneumonia",
            "COPD",
            "diabetes",
            "hypertension",
            "stroke",
            "sepsis",
            "heart failure",
        ],
        "treatments": [
            "aspirin",
            "antibiotics",
            "insulin",
            "ACE inhibitors",
            "beta blockers",
            "statins",
            "oxygen therapy",
            "IV fluids",
        ],
        "tests": ["ECG", "CBC", "CXR", "troponin", "D-dimer", "BNP", "CT scan", "MRI", "ultrasound"],
        "procedures": [
            "intubation",
            "catheterization",
            "surgery",
            "biopsy",
            "lumbar puncture",
            "chest tube",
        ],
    }

    REASONING_PATTERNS = [
        "symptom_to_differential",
        "differential_to_workup",
        "workup_to_diagnosis",
        "diagnosis_to_treatment",
        "treatment_to_monitoring",
    ]

    def get_name(self) -> str:
        """Get domain name."""
        return "medical"

    def extract_concepts(self, text: str) -> List[Concept]:
        """Extract medical concepts from text."""
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
                            confidence=0.9,
                            context=text[max(0, match.start() - 30) : match.end() + 30],
                            position=match.start(),
                        )
                    )

        return concepts

    def identify_relationships(self, concepts: List[Concept], text: str) -> List[Relationship]:
        """Identify medical relationships between concepts."""
        relationships = []
        text_lower = text.lower()

        # Medical-specific relationship patterns
        for i, source in enumerate(concepts):
            for target in concepts[i + 1 :]:
                rel_type = self._determine_medical_relationship(source, target, text_lower)
                if rel_type:
                    relationships.append(
                        Relationship(
                            source=source,
                            target=target,
                            type=rel_type,
                            confidence=0.85,
                            evidence=self._extract_evidence(source, target, text),
                        )
                    )

        return relationships

    def _determine_medical_relationship(self, source: Concept, target: Concept, text: str) -> str:
        """Determine medical relationship type."""
        # Symptom → Disease
        if source.type == "symptoms" and target.type == "diseases":
            return "indicates"

        # Disease → Test
        if source.type == "diseases" and target.type == "tests":
            return "diagnosed_by"

        # Test → Disease
        if source.type == "tests" and target.type == "diseases":
            return "confirms"

        # Disease → Treatment
        if source.type == "diseases" and target.type == "treatments":
            return "treated_with"

        # Treatment → Disease
        if source.type == "treatments" and target.type == "diseases":
            return "treats"

        # Treatment → Symptom
        if source.type == "treatments" and target.type == "symptoms":
            return "alleviates"

        return "relates_to"

    def _extract_evidence(self, source: Concept, target: Concept, text: str) -> str:
        """Extract evidence for relationship."""
        start = min(source.position, target.position)
        end = max(source.position + len(source.text), target.position + len(target.text))
        return text[max(0, start - 20) : min(len(text), end + 20)]

    def build_reasoning_chains(self, concepts: List[Concept], relationships: List[Relationship]) -> List[ReasoningChain]:
        """Build clinical reasoning chains."""
        chains = []

        # Build diagnostic chain: symptoms → tests → diagnosis → treatment
        diagnostic_chain = self._build_diagnostic_chain(concepts, relationships)
        if diagnostic_chain:
            chains.append(diagnostic_chain)

        # Build therapeutic chain: diagnosis → treatment → monitoring
        therapeutic_chain = self._build_therapeutic_chain(concepts, relationships)
        if therapeutic_chain:
            chains.append(therapeutic_chain)

        return chains

    def _build_diagnostic_chain(
        self, concepts: List[Concept], relationships: List[Relationship]
    ) -> ReasoningChain:
        """Build a diagnostic reasoning chain."""
        steps = []

        # Find symptom
        symptoms = [c for c in concepts if c.type == "symptoms"]
        if symptoms:
            steps.append(ReasoningStep(concept=symptoms[0], action="observe", rationale="Patient presentation"))

        # Find test
        tests = [c for c in concepts if c.type == "tests"]
        if tests:
            steps.append(
                ReasoningStep(
                    concept=tests[0], action="investigate", rationale="Order diagnostic workup"
                )
            )

        # Find diagnosis
        diseases = [c for c in concepts if c.type == "diseases"]
        if diseases:
            steps.append(
                ReasoningStep(concept=diseases[0], action="diagnose", rationale="Based on clinical findings")
            )

        # Find treatment
        treatments = [c for c in concepts if c.type == "treatments"]
        if treatments:
            steps.append(
                ReasoningStep(
                    concept=treatments[0], action="treat", rationale="Evidence-based management"
                )
            )

        if len(steps) >= 2:
            return ReasoningChain(type="diagnostic", steps=steps, confidence=0.8, domain="medical")
        return None

    def _build_therapeutic_chain(
        self, concepts: List[Concept], relationships: List[Relationship]
    ) -> Optional[ReasoningChain]:
        """Build a therapeutic reasoning chain."""
        steps = []

        # Find diagnosis
        diseases = [c for c in concepts if c.type == "diseases"]
        if diseases:
            steps.append(
                ReasoningStep(concept=diseases[0], action="diagnose", rationale="Clinical diagnosis")
            )

        # Find treatment
        treatments = [c for c in concepts if c.type == "treatments"]
        if treatments:
            steps.append(
                ReasoningStep(
                    concept=treatments[0], action="treat", rationale="Evidence-based treatment plan"
                )
            )

        # Find monitoring/test
        tests = [c for c in concepts if c.type == "tests"]
        if tests:
            steps.append(
                ReasoningStep(
                    concept=tests[0], action="monitor", rationale="Monitor treatment response"
                )
            )

        if len(steps) >= 2:
            return ReasoningChain(type="therapeutic", steps=steps, confidence=0.75, domain="medical")
        return None

    def generate_questions(self, content: Dict) -> List[str]:
        """Generate clinical questions."""
        questions = []

        if "diseases" in content:
            for disease in content["diseases"]:
                questions.append(f"What are the typical presenting symptoms of {disease}?")
                questions.append(f"What diagnostic tests are used to confirm {disease}?")
                questions.append(f"What is the first-line treatment for {disease}?")

        return questions

    def get_terminology_mapping(self) -> Dict:
        """Get medical terminology mapping."""
        return self.TERMINOLOGY

    def get_reasoning_patterns(self) -> List[str]:
        """Get clinical reasoning patterns."""
        return self.REASONING_PATTERNS
