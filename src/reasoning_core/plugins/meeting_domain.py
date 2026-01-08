"""Meeting domain plugin for agenda and note-taking extraction."""

from typing import List, Dict, Optional
from reasoning_core.plugins.base_domain import BaseDomain
from reasoning_core.extractors.concept_extractor import Concept
from reasoning_core.extractors.relationship_mapper import Relationship
from reasoning_core.extractors.reasoning_chain_builder import ReasoningChain, ReasoningStep
import re


class MeetingDomain(BaseDomain):
    """Meeting agenda and note-taking domain."""

    TERMINOLOGY = {
        "agenda_items": [
            "agenda",
            "discussion",
            "topic",
            "item",
            "point",
            "subject",
            "matter",
            "issue",
            "question",
            "proposal",
        ],
        "action_items": [
            "action",
            "todo",
            "task",
            "follow-up",
            "follow up",
            "assign",
            "assignment",
            "deliverable",
            "next step",
            "action required",
        ],
        "decisions": [
            "decided",
            "agreed",
            "approved",
            "resolution",
            "consensus",
            "decision",
            "conclusion",
            "determined",
            "resolved",
            "outcome",
        ],
        "participants": [
            "attendee",
            "participant",
            "present",
            "absent",
            "required",
            "optional",
            "organizer",
            "facilitator",
            "chair",
            "secretary",
        ],
        "outcomes": [
            "outcome",
            "result",
            "conclusion",
            "next steps",
            "summary",
            "takeaway",
            "finding",
            "recommendation",
        ],
        "dates": [
            "deadline",
            "due date",
            "timeline",
            "schedule",
            "meeting date",
            "follow-up date",
            "target date",
        ],
    }

    REASONING_PATTERNS = [
        "agenda_to_discussion",
        "discussion_to_decision",
        "decision_to_action",
        "action_to_owner",
        "owner_to_deadline",
        "action_to_outcome",
    ]

    def get_name(self) -> str:
        """Get domain name."""
        return "meeting"

    def extract_concepts(self, text: str) -> List[Concept]:
        """Extract meeting concepts from text."""
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
        """Identify meeting relationships between concepts."""
        relationships = []

        # Meeting-specific relationship patterns
        for i, source in enumerate(concepts):
            for target in concepts[i + 1 :]:
                rel_type = self._determine_meeting_relationship(source, target)
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

    def _determine_meeting_relationship(self, source: Concept, target: Concept) -> Optional[str]:
        """Determine meeting relationship type."""
        # Agenda → Discussion
        if source.type == "agenda_items" and target.type == "agenda_items":
            return "discussed_in"

        # Discussion → Decision
        if source.type == "agenda_items" and target.type == "decisions":
            return "leads_to"

        # Decision → Action
        if source.type == "decisions" and target.type == "action_items":
            return "requires"

        # Action → Participant (owner)
        if source.type == "action_items" and target.type == "participants":
            return "assigned_to"

        # Action → Deadline
        if source.type == "action_items" and target.type == "dates":
            return "due_by"

        # Decision → Outcome
        if source.type == "decisions" and target.type == "outcomes":
            return "produces"

        # Participant → Action (alternative direction)
        if source.type == "participants" and target.type == "action_items":
            return "responsible_for"

        return "relates_to"

    def _extract_evidence(self, source: Concept, target: Concept, text: str) -> str:
        """Extract evidence for relationship."""
        start = min(source.position, target.position)
        end = max(source.position + len(source.text), target.position + len(target.text))
        return text[max(0, start - 20) : min(len(text), end + 20)]

    def build_reasoning_chains(
        self, concepts: List[Concept], relationships: List[Relationship]
    ) -> List[ReasoningChain]:
        """Build meeting reasoning chains."""
        chains = []

        # Build action chain: agenda → discussion → decision → action → owner
        action_chain = self._build_action_chain(concepts, relationships)
        if action_chain:
            chains.append(action_chain)

        # Build outcome chain: decision → action → outcome
        outcome_chain = self._build_outcome_chain(concepts, relationships)
        if outcome_chain:
            chains.append(outcome_chain)

        return chains

    def _build_action_chain(
        self, concepts: List[Concept], relationships: List[Relationship]
    ) -> Optional[ReasoningChain]:
        """Build an action item chain."""
        steps = []

        # Find agenda item
        agenda_items = [c for c in concepts if c.type == "agenda_items"]
        if agenda_items:
            steps.append(
                ReasoningStep(concept=agenda_items[0], action="discuss", rationale="Meeting agenda item")
            )

        # Find decision
        decisions = [c for c in concepts if c.type == "decisions"]
        if decisions:
            steps.append(
                ReasoningStep(concept=decisions[0], action="decide", rationale="Consensus reached")
            )

        # Find action item
        actions = [c for c in concepts if c.type == "action_items"]
        if actions:
            steps.append(
                ReasoningStep(concept=actions[0], action="assign", rationale="Action item created")
            )

        # Find owner
        participants = [c for c in concepts if c.type == "participants"]
        if participants:
            steps.append(
                ReasoningStep(
                    concept=participants[0], action="own", rationale="Action assigned to participant"
                )
            )

        if len(steps) >= 2:
            return ReasoningChain(type="action", steps=steps, confidence=0.75, domain="meeting")
        return None

    def _build_outcome_chain(
        self, concepts: List[Concept], relationships: List[Relationship]
    ) -> Optional[ReasoningChain]:
        """Build an outcome chain."""
        steps = []

        # Find decision
        decisions = [c for c in concepts if c.type == "decisions"]
        if decisions:
            steps.append(
                ReasoningStep(concept=decisions[0], action="decide", rationale="Meeting decision")
            )

        # Find action
        actions = [c for c in concepts if c.type == "action_items"]
        if actions:
            steps.append(
                ReasoningStep(concept=actions[0], action="execute", rationale="Action taken")
            )

        # Find outcome
        outcomes = [c for c in concepts if c.type == "outcomes"]
        if outcomes:
            steps.append(
                ReasoningStep(concept=outcomes[0], action="achieve", rationale="Outcome reached")
            )

        if len(steps) >= 2:
            return ReasoningChain(type="outcome", steps=steps, confidence=0.7, domain="meeting")
        return None

    def generate_questions(self, content: Dict) -> List[str]:
        """Generate meeting questions."""
        questions = []

        if "action_items" in content:
            for action in content["action_items"]:
                questions.append(f"Who is responsible for {action}?")
                questions.append(f"What is the deadline for {action}?")
                questions.append(f"What was the decision that led to {action}?")

        if "decisions" in content:
            for decision in content["decisions"]:
                questions.append(f"What was the outcome of {decision}?")
                questions.append(f"Who participated in {decision}?")

        if "agenda_items" in content:
            for item in content["agenda_items"]:
                questions.append(f"Was {item} resolved?")
                questions.append(f"What were the key points about {item}?")

        return questions

    def get_terminology_mapping(self) -> Dict:
        """Get meeting terminology mapping."""
        return self.TERMINOLOGY

    def get_reasoning_patterns(self) -> List[str]:
        """Get meeting reasoning patterns."""
        return self.REASONING_PATTERNS
