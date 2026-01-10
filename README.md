# Reasoning Core 🧠

**Universal reasoning extraction engine - Transform expertise into intelligent knowledge graphs**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Reasoning Core is a Python library that extracts expert reasoning patterns from text and builds intelligent knowledge graphs. It transforms unstructured expertise into structured, queryable knowledge.

## ✨ Features

- **🔍 Concept Extraction**: Identify domain-specific concepts automatically
- **🔗 Relationship Mapping**: Discover connections between concepts
- **⛓️ Reasoning Chains**: Build step-by-step reasoning patterns
- **📊 Knowledge Graphs**: Create visual, queryable knowledge structures
- **🎯 Multi-Domain Support**: Medical, business, legal, engineering, and custom domains
- **🔌 Plugin Architecture**: Extensible domain-specific reasoning
- **⚡ Async Support**: Non-blocking processing for real-time applications
- **🚀 Production Ready**: Type-safe, tested, documented

## 🚀 Quick Start

### Installation

```bash
pip install reasoning-core
```

### Basic Usage

```python
from reasoning_core import ReasoningAPI, MedicalDomain

# Initialize with a domain
api = ReasoningAPI(domain=MedicalDomain())

# Process text
text = """
Patient presents with chest pain and shortness of breath.
ECG shows ST elevation. Troponin is elevated.
Diagnosis: Myocardial infarction.
Treatment: Aspirin, heparin, and catheterization.
"""

result = api.process_text(text)

# Access extracted reasoning
print(f"Concepts: {len(result['concepts'])}")
print(f"Relationships: {len(result['relationships'])}")
print(f"Reasoning chains: {len(result['reasoning_chains'])}")
print(f"Generated questions: {result['questions']}")
```

### Async Usage (New! ⚡)

```python
import asyncio
from reasoning_core import AsyncReasoningAPI, MedicalDomain

async def process_transcription():
    api = AsyncReasoningAPI(domain=MedicalDomain())
    
    # Non-blocking processing
    result = await api.process_text_async(text)
    
    # Process streaming transcription
    async for chunk_result in api.process_stream(transcription_stream):
        print(f"Processed chunk {chunk_result['chunk_num']}")
    
    # Batch process multiple documents concurrently
    results = await api.process_batch([doc1, doc2, doc3])

asyncio.run(process_transcription())
```

### Domain-Specific Extraction

```python
# Medical Domain
from reasoning_core import MedicalDomain
medical_api = ReasoningAPI(domain=MedicalDomain())

# Business Domain
from reasoning_core import BusinessDomain
business_api = ReasoningAPI(domain=BusinessDomain())

# Meeting Domain
from reasoning_core import MeetingDomain
meeting_api = ReasoningAPI(domain=MeetingDomain())

# Generic (no domain)
generic_api = ReasoningAPI()
```

## 📚 Core Components

### Concept Extractor

Extracts domain-specific concepts from text:

```python
from reasoning_core import ConceptExtractor, MedicalDomain

extractor = ConceptExtractor(domain=MedicalDomain())
concepts = extractor.extract("Patient has fever and cough")

for concept in concepts:
    print(f"{concept.text} ({concept.type}) - confidence: {concept.confidence}")
```

### Relationship Mapper

Identifies relationships between concepts:

```python
from reasoning_core import RelationshipMapper

mapper = RelationshipMapper(domain=MedicalDomain())
relationships = mapper.map_relationships(concepts, text)

for rel in relationships:
    print(f"{rel.source.text} --[{rel.type}]--> {rel.target.text}")
```

### Reasoning Chain Builder

Builds step-by-step reasoning patterns:

```python
from reasoning_core import ReasoningChainBuilder

builder = ReasoningChainBuilder(domain=MedicalDomain())
chains = builder.build_chains(concepts, relationships)

for chain in chains:
    print(f"Chain type: {chain.type}")
    for step in chain.steps:
        print(f"  {step.action}: {step.concept.text} - {step.rationale}")
```

### Knowledge Graph

Create and query knowledge graphs:

```python
from reasoning_core.graph import KnowledgeGraph, Node, Edge

graph = KnowledgeGraph()

# Add nodes
graph.add_node(Node(id="fever", type="symptom", label="Fever"))
graph.add_node(Node(id="infection", type="disease", label="Infection"))

# Add edges
graph.add_edge(Edge(source_id="fever", target_id="infection", type="indicates"))

# Query
path = graph.find_path("fever", "infection")
print(f"Path: {path}")

# Export in multiple formats
print(graph.to_json())        # JSON
print(graph.to_dot())         # Graphviz DOT
print(graph.to_graphml())     # GraphML XML
print(graph.to_cytoscape())   # Cytoscape.js
```

## ⚡ Async API (Real-Time Processing)

The `AsyncReasoningAPI` enables non-blocking processing for real-time applications like live transcription, streaming audio, and large document processing.

### Streaming Processing

Process text as it arrives (perfect for CogniScribe integration):

```python
import asyncio
from reasoning_core import AsyncReasoningAPI, MedicalDomain

async def process_live_transcription(transcription_stream):
    api = AsyncReasoningAPI(domain=MedicalDomain())
    
    # Process stream with overlap for context preservation
    async for result in api.process_stream(
        transcription_stream,
        chunk_size=1000,  # Process every 1000 characters
        overlap=100,      # 100 character overlap for context
        progress_callback=lambda n, t: print(f"Processing chunk {n}")
    ):
        # Extract concepts from each chunk
        concepts = result['concepts']
        chains = result['reasoning_chains']
        
        # Update UI, database, or knowledge graph in real-time
        print(f"Chunk {result['chunk_num']}: {len(concepts)} concepts")
```

### Batch Processing

Process multiple documents concurrently:

```python
async def process_multiple_lectures(lecture_transcripts):
    api = AsyncReasoningAPI(domain=MedicalDomain(), max_workers=4)
    
    # Process all lectures concurrently
    results = await api.process_batch(
        lecture_transcripts,
        progress_callback=lambda done, total: print(f"{done}/{total} complete")
    )
    
    # Analyze all results
    for i, result in enumerate(results):
        print(f"Lecture {i+1}: {len(result['concepts'])} concepts")
```

### Merging Stream Results

Combine streaming results into unified output:

```python
async def process_and_merge(long_transcript):
    api = AsyncReasoningAPI(domain=MedicalDomain())
    
    # Process as stream
    stream_results = api.process_stream(transcript_stream, chunk_size=500)
    
    # Merge into single unified result
    merged = await api.merge_stream_results(stream_results)
    
    print(f"Total concepts: {len(merged['concepts'])}")
    print(f"Total relationships: {len(merged['relationships'])}")
    print(f"Processed {merged['chunk_count']} chunks")
    
    # Access unified knowledge graph
    graph = merged['knowledge_graph']
```

### Use Cases for Async API

- **Live Medical Transcription**: Process CogniScribe transcriptions in real-time
- **Meeting Notes**: Extract action items and decisions as meetings progress
- **Large Document Processing**: Process lengthy documents without blocking
- **Concurrent Analysis**: Analyze multiple documents simultaneously
- **Progress Tracking**: Monitor processing of long-running operations

## 🎯 Domain Plugins

### Medical Domain

Clinical reasoning for medical education:

```python
from reasoning_core import MedicalDomain

domain = MedicalDomain()
print(domain.get_reasoning_patterns())
# ['symptom_to_differential', 'differential_to_workup', 
#  'workup_to_diagnosis', 'diagnosis_to_treatment']
```

**Concepts extracted:**
- Symptoms (pain, fever, cough)
- Diseases (MI, pneumonia, COPD)
- Treatments (aspirin, antibiotics)
- Tests (ECG, CBC, troponin)
- Procedures (intubation, catheterization)

### Business Domain

Business strategy and sales reasoning:

```python
from reasoning_core import BusinessDomain

domain = BusinessDomain()
print(domain.get_reasoning_patterns())
# ['problem_to_solution', 'objection_to_response',
#  'feature_to_benefit', 'pain_to_value']
```

**Concepts extracted:**
- Strategies (upselling, objection handling)
- Metrics (conversion rate, LTV, ROI)
- Frameworks (MEDDIC, BANT, SPIN)
- Activities (prospecting, discovery, closing)
- Pain points (inefficiency, cost, complexity)

### Meeting Domain

Meeting notes and action item extraction:

```python
from reasoning_core import MeetingDomain

domain = MeetingDomain()
print(domain.get_reasoning_patterns())
# ['agenda_to_discussion', 'discussion_to_decision',
#  'decision_to_action', 'action_to_owner']
```

**Concepts extracted:**
- Action items and tasks
- Decisions and agreements
- Participants and roles
- Deadlines and timelines
- Discussion topics

### Custom Domains

Create your own domain plugin:

```python
from reasoning_core.plugins import BaseDomain

class MyCustomDomain(BaseDomain):
    def get_name(self) -> str:
        return "custom"
    
    def extract_concepts(self, text: str):
        # Your custom extraction logic
        pass
    
    def identify_relationships(self, concepts, text):
        # Your custom relationship logic
        pass
    
    # Implement other required methods...

api = ReasoningAPI(domain=MyCustomDomain())
```

## 🏗️ Architecture

```
Text Input
    ↓
┌────────────────────┐
│ Concept Extractor  │ → Identifies key concepts
└─────────┬──────────┘
          ↓
┌────────────────────┐
│Relationship Mapper │ → Maps connections
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Chain Builder      │ → Builds reasoning patterns
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Knowledge Graph    │ → Structures knowledge
└────────────────────┘
```

## 📦 Installation from Source

```bash
git clone https://github.com/Excelsior2026/reasoning-core.git
cd reasoning-core
pip install -e .
```

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run async tests
pytest -v tests/test_async_api.py

# Format code
black src tests
isort src tests

# Lint
flake8 src tests
mypy src
```

## 🎯 Use Cases

### Medical Education (CogniScribe Integration)
- Extract clinical reasoning from live lectures
- Build diagnostic decision trees in real-time
- Generate study questions from transcriptions
- Create interactive knowledge graphs

```python
# CogniScribe integration example
async def cogniscribe_pipeline(audio_stream):
    # Audio → Text (CogniScribe STT)
    transcription = await cogniscribe.transcribe(audio_stream)
    
    # Text → Reasoning (reasoning-core)
    api = AsyncReasoningAPI(domain=MedicalDomain())
    async for result in api.process_stream(transcription):
        # Update knowledge graph in real-time
        await update_knowledge_base(result)
```

### Business Training
- Capture sales methodologies from recordings
- Map objection handling strategies
- Identify success patterns
- Build training materials

### Legal Analysis
- Extract case law reasoning
- Map precedent relationships
- Build argument structures

### Engineering Documentation
- Capture architectural decisions
- Map system dependencies
- Document troubleshooting patterns

## 📖 Examples

See the `examples/` directory for comprehensive usage examples:
- `async_usage_examples.py` - Async API usage patterns
- Jupyter notebooks for interactive exploration

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

Built for the COGNISCRIBE and REASONMAP projects.

---

**Made with ❤️ for transforming expertise into knowledge**
