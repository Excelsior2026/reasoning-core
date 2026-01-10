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
- **🚀 Production Ready**: Type-safe, tested, documented

## 🚀 Quick Start

### Installation Options

#### Option 1: Installer Packages (Recommended)

**macOS**: Download and run `ReasoningCore-0.1.0-macos.pkg`  
**Windows**: Download and run `ReasoningCore-0.1.0-windows-setup.exe` (as Administrator)

These installers automatically:
- Install Python 3.9+ (if needed)
- Install Node.js (if needed)
- Install all dependencies
- Set up the application

See [LOCAL_INSTALL.md](LOCAL_INSTALL.md) for details.

#### Option 2: From PyPI

```bash
pip install reasoning-core
```

#### Option 3: Unified Installer (Recommended for Local Use)

**macOS/Linux:**
```bash
./install-unified.sh
```

**Windows:**
```cmd
install-unified.bat
```

This unified installer automatically:
- ✅ Checks and installs all dependencies
- ✅ Starts the servers automatically
- ✅ Opens both API and Web UI

To install without starting:
```bash
./install-unified.sh --no-start  # macOS/Linux
install-unified.bat --no-start    # Windows
```

#### Option 4: Local Installation Script

```bash
./install.sh
```

This script checks prerequisites and installs all dependencies (without starting servers).

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

### Domain-Specific Extraction

```python
# Medical Domain
from reasoning_core import MedicalDomain
medical_api = ReasoningAPI(domain=MedicalDomain())

# Business Domain
from reasoning_core import BusinessDomain
business_api = ReasoningAPI(domain=BusinessDomain())

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

# Export
print(graph.to_json())
```

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

### Quick Install & Start

**macOS/Linux:**
```bash
git clone https://github.com/Excelsior2026/reasoning-core.git
cd reasoning-core
./install-unified.sh
```

**Windows:**
```cmd
git clone https://github.com/Excelsior2026/reasoning-core.git
cd reasoning-core
install-unified.bat
```

This will install everything and start the servers automatically!

### Quick Start (if already installed)

**macOS/Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

### Manual Install

```bash
git clone https://github.com/Excelsior2026/reasoning-core.git
cd reasoning-core
./install.sh
```

### Manual Install

```bash
git clone https://github.com/Excelsior2026/reasoning-core.git
cd reasoning-core
pip install -e .
pip install -r requirements-web.txt
cd web && npm install && cd ..
```

### Building Installers

To create installer packages for macOS or Windows, see [installers/BUILD_INSTRUCTIONS.md](installers/BUILD_INSTRUCTIONS.md).

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Format code
black src tests
isort src tests

# Lint
flake8 src tests
mypy src
```

## 🎯 Use Cases

### Medical Education
- Extract clinical reasoning from lectures
- Build diagnostic decision trees
- Generate study questions

### Business Training
- Capture sales methodologies
- Map objection handling strategies
- Identify success patterns

### Legal Analysis
- Extract case law reasoning
- Map precedent relationships
- Build argument structures

### Engineering Documentation
- Capture architectural decisions
- Map system dependencies
- Document troubleshooting patterns

## 📖 Documentation

Full documentation coming soon at: [docs.reasoning-core.dev](https://docs.reasoning-core.dev)

## 🤝 Contributing

Contributions are welcome! Areas for contribution:
- New domain plugins
- Enhanced extraction algorithms
- Graph visualization tools
- Integration examples

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

Built for the COGNISCRIBE and REASONMAP projects.

---

**Made with ❤️ for transforming expertise into knowledge**
