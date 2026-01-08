# Code Review: reasoning-core

**Date:** 2026-01-XX  
**Reviewer:** AI Code Reviewer  
**Version:** 0.1.0

## Executive Summary

The reasoning-core repository is a well-structured Python library designed to be integrated into **CogniScribe** for extracting reasoning patterns from text and building knowledge graphs/mind maps. The codebase demonstrates good organization, comprehensive test coverage, and a clear plugin architecture for multi-domain use (medical education, meeting notes, agenda processing, etc.). However, there are several areas for improvement including error handling, code duplication, type safety, and documentation.

**Use Case Context:**
- **Primary:** Integrated into CogniScribe to extract reasoning patterns and build knowledge graphs from transcribed medical lectures
- **Secondary:** Reusable for meeting agendas, note-taking systems, and other document analysis workflows
- **Architecture:** Plugin-based domain system (medical, business, generic) for flexibility across use cases

**Overall Assessment:** ✅ **Good** - Solid foundation with room for improvement

**Key Strengths:**
- Clean architecture with plugin system (perfect for multi-domain reuse)
- Good test coverage
- Well-organized codebase
- Clear separation of concerns
- Designed for integration (good API structure)

**Key Issues:**
- Missing error handling throughout
- Duplicate domain/plugin structure needs clarification
- Incomplete type hints
- Limited input validation
- Missing ReasoningAPI export in __init__.py
- Need meeting/agenda domain plugin for note-taking use case

---

## 1. Architecture & Design

### 1.1 Overall Structure ✅
The codebase follows a clean architecture pattern:
- `api/` - High-level API
- `extractors/` - Core extraction logic
- `graph/` - Knowledge graph implementation
- `plugins/` - Domain-specific implementations

**Recommendation:** Maintain this structure, it's well-organized.

### 1.2 Duplicate Domain/Plugin Structure ⚠️ **CRITICAL**

**Issue:** Two separate directory structures exist:
- `src/reasoning_core/domains/` (different interface - uses dataclasses with different structure)
- `src/reasoning_core/plugins/` (current implementation - used by API)

The `__init__.py` imports from `plugins`, but `domains` also exists with a different `BaseDomain` interface that uses different `Concept` and `Relationship` dataclasses.

**Files:**
- `src/reasoning_core/domains/base_domain.py` - Different interface (uses `Concept` with `name`, `metadata` fields)
- `src/reasoning_core/plugins/base_domain.py` - Current interface (uses `Concept` with `text`, `position` fields)
- `src/reasoning_core/domains/medical_domain.py` - Unused? Different implementation
- `src/reasoning_core/plugins/medical_domain.py` - Active, used by ReasoningAPI

**Context:** Given this is for integration into CogniScribe, having two structures creates confusion about which one to use.

**Impact:** 
- Confusion for integration
- Maintenance burden
- Potential import errors if someone imports from wrong location
- Unclear which is "correct" for new domains

**Recommendation:**
1. **Remove unused `domains/` directory** if it's legacy code
2. **OR** If `domains/` was meant for a different purpose, document the distinction:
   - `plugins/` = For ReasoningAPI integration (current)
   - `domains/` = Alternative implementation? Remove if not needed
3. **Add clear documentation** about which structure to use for new domain plugins
4. **Update CogniScribe integration** to ensure it uses the `plugins/` structure consistently

```python
# Recommended action:
# If domains/ is legacy: DELETE it to avoid confusion
# If domains/ has a purpose: Document clearly and consider renaming
```

### 1.3 Plugin Architecture ✅
The plugin system is well-designed with `BaseDomain` abstract class. Good use of ABC.

**Minor Issue:** Some domain methods have inconsistent return types (e.g., `_build_therapeutic_chain` returns `None` instead of empty list).

---

## 2. Code Quality

### 2.1 Error Handling ❌ **MAJOR ISSUE**

**Issue:** No error handling or exception management throughout the codebase.

**Examples:**

#### `reasoning_api.py:36`
```python
concepts = self.concept_extractor.extract(text)  # No error handling
```

**Impact:**
- API failures on invalid input
- No graceful degradation
- Poor user experience

**Recommendation:**
```python
def process_text(self, text: str, include_graph: bool = True) -> Dict:
    """Process text and extract reasoning."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text.strip():
        raise ValueError("text cannot be empty")
    
    try:
        concepts = self.concept_extractor.extract(text)
        relationships = self.relationship_mapper.map_relationships(concepts, text)
        chains = self.chain_builder.build_chains(concepts, relationships)
        # ...
    except Exception as e:
        raise ProcessingError(f"Failed to process text: {e}") from e
```

**Files Needing Error Handling:**
- `reasoning_api.py` - All public methods
- `concept_extractor.py` - Extract methods
- `relationship_mapper.py` - Mapping methods
- `reasoning_chain_builder.py` - Chain building
- `knowledge_graph.py` - Graph operations

### 2.2 Input Validation ⚠️

**Issue:** Limited validation of inputs.

**Examples:**
- `reasoning_api.py:14` - No validation that `domain` implements `BaseDomain`
- `knowledge_graph.py:39` - No validation of Node structure
- `knowledge_graph.py:49` - No validation that nodes exist before adding edges

**Recommendation:**
```python
def add_edge(self, edge: Edge) -> None:
    """Add an edge to the graph."""
    if edge.source_id not in self.nodes:
        raise ValueError(f"Source node '{edge.source_id}' not found")
    if edge.target_id not in self.nodes:
        raise ValueError(f"Target node '{edge.target_id}' not found")
    # ... rest of method
```

### 2.3 Type Hints ⚠️ **PARTIAL**

**Issue:** Inconsistent type hints throughout codebase.

**Examples:**

#### `concept_extractor.py:22`
```python
def __init__(self, domain=None):  # Should be Optional[BaseDomain]
```

#### `reasoning_api.py:45`
```python
result = {
    "concepts": [vars(c) for c in concepts],  # Using vars() loses type info
```

#### `knowledge_graph.py:92`
```python
def get_edges_from(self, node_id: str) -> List[Edge]:
    return [edge for edge in self.edges if edge.source_id == node_id]
    # Should filter type to avoid edge.source_id being None
```

**Recommendation:**
- Add complete type hints to all public APIs
- Use `TypedDict` for return dictionaries
- Add `from __future__ import annotations` for forward references

### 2.4 Code Duplication ⚠️

**Issue:** Some logic is duplicated.

**Examples:**

#### Evidence extraction duplicated:
- `medical_domain.py:143` - `_extract_evidence`
- `business_domain.py:131` - `_extract_evidence`
- `relationship_mapper.py:154` - `_get_evidence`

**Recommendation:** Move to base class or utility function.

#### Concept extraction pattern duplicated:
- `medical_domain.py:71` - Similar to `business_domain.py:69`

**Recommendation:** Extract common pattern to `BaseDomain`.

---

## 3. Documentation

### 3.1 Docstrings ✅ **GOOD**
Most functions have docstrings with Args/Returns. Good use of Google style.

### 3.2 API Documentation ⚠️

**Issue:** `ReasoningAPI` not exported in main `__init__.py`.

**Current:**
```python:src/reasoning_core/__init__.py
# ReasoningAPI is not in __all__
```

**Recommendation:**
```python
from reasoning_core.api.reasoning_api import ReasoningAPI

__all__ = [
    # ... existing ...
    "ReasoningAPI",
]
```

### 3.3 README vs Code ⚠️

**Issue:** README shows usage that doesn't match actual implementation.

**README shows:**
```python
from reasoning_core import ReasoningAPI, MedicalDomain
```

**But `__init__.py` doesn't export `ReasoningAPI`** (see above).

---

## 4. Data Structures

### 4.1 Dataclasses ✅ **GOOD**
Good use of `@dataclass` for `Concept`, `Relationship`, `ReasoningStep`, etc.

**Minor Issue:** Some dataclasses use `field(default_factory=dict)` but don't check for `None` in `__post_init__`.

### 4.2 Knowledge Graph Implementation ✅

**Strengths:**
- Clean API
- Good serialization support
- Efficient adjacency list representation

**Issues:**

#### `knowledge_graph.py:105` - Path finding bug
```python
def find_path(self, start_id: str, end_id: str, max_depth: int = 5) -> Optional[List[str]]:
    # ...
    if dfs(start_id, 0):
        path.append(end_id)
        return path
    return None
```

**Problem:** The `visited` set and `path` list are shared across recursive calls incorrectly. The DFS implementation has a bug where `visited.remove()` happens after popping, which could cause issues.

**Recommendation:** Review and fix DFS implementation.

#### `knowledge_graph.py:217` - Edge duplication
```python
def merge(self, other: "KnowledgeGraph") -> None:
    for edge in other.edges:
        self.add_edge(edge)  # Could add duplicate edges
```

**Issue:** No check for existing edges. Should validate before adding.

---

## 5. Domain Plugins

### 5.1 Medical Domain ✅ **GOOD**

**Strengths:**
- Comprehensive terminology
- Clear reasoning patterns
- Well-suited for CogniScribe medical education use case

**Issues:**

#### `medical_domain.py:209` - Incomplete implementation
```python
def _build_therapeutic_chain(...) -> ReasoningChain:
    """Build a therapeutic reasoning chain."""
    return None  # Placeholder
```

**Recommendation:** Implement or remove if not needed.

#### `medical_domain.py:78-89` - Case sensitivity
```python
pattern = r"\b" + re.escape(term.lower()) + r"\b"
for match in re.finditer(pattern, text_lower):
    concepts.append(
        Concept(
            text=term,  # Uses original term, not matched text
```

**Issue:** If term is "MI" and text has "mi", it still extracts but position might be wrong. Consider preserving case from match.

### 5.2 Business Domain ✅ **GOOD**

Similar structure to medical domain. Same issues apply (duplication, case sensitivity).

**Note:** Business domain may be useful for meeting/agenda processing, but consider a dedicated **MeetingDomain** or **AgendaDomain** plugin for meeting note-taking use case.

### 5.3 Missing Domain: Meeting/Agenda Domain ❌ **RECOMMENDED**

**Issue:** For the meeting agenda and note-taking use case, there's no dedicated domain plugin.

**Current State:**
- `BusinessDomain` exists but is focused on sales/business strategy
- No specific domain for meeting agendas, action items, decisions, etc.

**Recommendation:** Create a `MeetingDomain` plugin with:

```python
class MeetingDomain(BaseDomain):
    TERMINOLOGY = {
        "agenda_items": ["agenda", "discussion", "topic", "item"],
        "action_items": ["action", "todo", "task", "follow-up", "assign"],
        "decisions": ["decided", "agreed", "approved", "resolution", "consensus"],
        "participants": ["attendee", "present", "absent", "required"],
        "outcomes": ["outcome", "result", "conclusion", "next steps"],
        "dates": ["deadline", "due date", "timeline", "schedule"],
    }
    
    REASONING_PATTERNS = [
        "agenda_to_discussion",
        "discussion_to_decision",
        "decision_to_action",
        "action_to_owner",
        "owner_to_deadline",
    ]
```

This would extract:
- Meeting topics from agendas
- Action items and owners
- Decisions made
- Follow-up items
- Participant assignments

Perfect for CogniScribe meeting note integration!

---

## 6. Testing

### 6.1 Coverage ✅ **GOOD**
Good test coverage with pytest. Test structure is clear.

**Issues:**

#### Missing tests:
- Error handling paths
- Edge cases (very long text, special characters)
- Invalid input scenarios
- Graph edge cases (cycles, disconnected nodes)

#### `test_api.py:88`
```python
# No questions without domain
assert "questions" not in result or len(result["questions"]) == 0
```

**Issue:** Inconsistent assertion - should be more explicit.

### 6.2 Test Fixtures ✅ **GOOD**
Good use of pytest fixtures in `conftest.py`.

---

## 7. Performance

### 7.1 Algorithmic Concerns ⚠️

#### `relationship_mapper.py:76`
```python
for i, source in enumerate(concepts):
    for target in concepts[i + 1:]:  # O(n²) - okay for small n
```

**Note:** O(n²) is acceptable for small concept lists, but could be optimized with spatial indexing for large texts.

#### `reasoning_chain_builder.py:123`
```python
def dfs(current: Concept, path: List[Concept], depth: int):
    # DFS with no cycle detection beyond visited set
```

**Issue:** `visited` set usage could prevent finding all paths. Consider using a path-based visited set instead.

### 7.2 Memory ⚠️

**Issue:** Large text processing might create many intermediate objects. Consider:
- Streaming processing for large texts
- Memory-efficient data structures
- Lazy evaluation where possible

---

## 8. Security

### 8.1 Input Sanitization ⚠️

**Issue:** No sanitization of user input before processing.

**Recommendation:**
- Validate text length limits
- Sanitize special characters if needed
- Consider DoS protection for very large texts

### 8.2 Dependency Security ✅

Dependencies look minimal and standard (pydantic, pytest). Good!

---

## 9. Configuration

### 9.1 Hard-coded Values ⚠️

**Examples:**
- `concept_extractor.py:84` - `window=50` hard-coded
- `relationship_mapper.py:96` - `max_distance=100` hard-coded
- `reasoning_chain_builder.py:84` - `max_depth=5` hard-coded

**Recommendation:** Make these configurable via domain or API config.

---

## 10. Integration Considerations for CogniScribe

### 10.1 Integration Points ✅

**Current State:**
- `ReasoningAPI` provides clean interface for integration
- Knowledge graph output can be consumed by CogniScribe
- Domain plugins allow medical-specific extraction

**Recommendation for CogniScribe Integration:**

1. **Add reasoning extraction to CogniScribe pipeline:**
```python
# In CogniScribe pipeline after transcription
from reasoning_core import ReasoningAPI, MedicalDomain

api = ReasoningAPI(domain=MedicalDomain())
reasoning_result = api.process_text(transcript_text)

# Extract knowledge graph for visualization
knowledge_graph = reasoning_result["knowledge_graph"]
# Use in CogniScribe to generate mind maps/knowledge graphs
```

2. **Create meeting/agenda domain** (see Section 5.3)

3. **Export graph in formats useful for visualization:**
   - JSON (already exists) ✅
   - GraphML for visualization tools
   - DOT format for Graphviz
   - Cytoscape.js format for web visualization

### 10.2 Performance Considerations for Real-Time Use ⚠️

**Issue:** For meeting note-taking, may need near-real-time processing.

**Current:** Processing is synchronous and may be slow for large transcripts.

**Recommendation:**
- Add async support to `ReasoningAPI`
- Consider streaming/chunked processing for long texts
- Cache domain terminology lookups

### 10.3 Error Handling for Integration ⚠️

**Issue:** When integrated into CogniScribe, failures should be graceful.

**Recommendation:**
- Add fallback to generic domain if medical domain fails
- Return partial results on errors (not all-or-nothing)
- Log errors but don't crash the entire pipeline

---

## 11. Specific Code Issues

### 11.1 `reasoning_api.py:45-47`
```python
result = {
    "concepts": [vars(c) for c in concepts],  # Using vars()
```

**Issue:** `vars()` doesn't work well with dataclasses. Use `asdict()` from dataclasses or implement `to_dict()` methods.

**Recommendation:**
```python
from dataclasses import asdict

result = {
    "concepts": [asdict(c) for c in concepts],
    "relationships": [asdict(r) for r in relationships],
    # ...
}
```

### 11.2 `reasoning_api.py:78`
```python
id=f"{concept.type}_{concept.position}",  # Could have collisions
```

**Issue:** Multiple concepts of same type at same position = ID collision.

**Recommendation:** Use UUID or hash-based IDs.

### 11.3 `concept_extractor.py:100-124`
```python
def extract_with_llm(self, text: str, llm_service) -> List[Concept]:
    # Placeholder for LLM-based extraction
    # TODO: Implement LLM call
    return self.extract(text)
```

**Issue:** Method doesn't do what it says. Either implement or remove/document as placeholder.

### 11.4 `knowledge_graph.py:228`
```python
"avg_degree": len(self.edges) / max(len(self.nodes), 1),
```

**Issue:** This calculates average degree incorrectly. Should be `sum(degrees) / len(nodes)` or `2 * edges / nodes` for undirected.

---

## Priority Recommendations

### 🔴 **CRITICAL** (Fix Immediately)
1. **Remove or consolidate duplicate domain/plugin structure** (clarify domains/ vs plugins/)
2. **Add error handling to all public APIs** (critical for CogniScribe integration)
3. **Fix ReasoningAPI export in __init__.py** (prevents proper imports)
4. **Fix knowledge graph path finding bug** (affects graph quality)

### 🟠 **HIGH** (Fix Soon)
5. **Create MeetingDomain plugin** (for agenda/note-taking use case)
6. Add input validation
7. Complete type hints
8. Fix ID collision issue in graph node creation
9. Implement or remove `extract_with_llm` placeholder
10. Fix `_build_therapeutic_chain` implementation
11. Add graph export formats for visualization (GraphML, DOT, Cytoscape JSON)

### 🟡 **MEDIUM** (Improve Over Time)
12. Extract duplicate code to base classes/utilities
13. Make hard-coded values configurable
14. Add missing test cases
15. Improve documentation consistency
16. Optimize performance for large inputs
17. Add async support for real-time meeting processing
18. Add integration examples for CogniScribe
19. Add graph visualization utilities/helpers

### 🟢 **LOW** (Nice to Have)
15. Add cycle detection in graph algorithms
16. Improve edge case handling
17. Add performance benchmarks
18. Consider streaming for large texts

---

## Conclusion

The reasoning-core library has a solid foundation with good architecture and test coverage, **perfectly positioned for integration into CogniScribe** and reuse for meeting/agenda note-taking systems. The plugin architecture is well-designed for multi-domain use.

The main concerns are:

1. **Error handling** - Critical for CogniScribe integration (needs graceful failures)
2. **Code duplication** - Domain/plugin structure needs consolidation (remove unused `domains/`)
3. **Type safety** - Needs completion for better IDE support
4. **Documentation consistency** - README should match code
5. **Missing MeetingDomain** - Needed for meeting/agenda use case

**For CogniScribe Integration:**
- ✅ API structure is integration-ready
- ✅ Knowledge graph output suitable for visualization
- ⚠️ Needs error handling for production use
- ⚠️ Needs MeetingDomain for meeting notes
- ⚠️ May benefit from async support for real-time processing

With these fixes, the library would be production-ready for both medical education and meeting note-taking use cases. The codebase shows good Python practices and maintainability.

---

## Review Checklist

- [x] Architecture review
- [x] Code quality review
- [x] Error handling review
- [x] Type safety review
- [x] Documentation review
- [x] Testing review
- [x] Performance considerations
- [x] Security review
- [x] Specific bug identification

---

**Next Steps:**
1. Review this document with the team
2. Prioritize fixes based on project timeline
3. Create GitHub issues for critical items
4. Schedule follow-up review after fixes
