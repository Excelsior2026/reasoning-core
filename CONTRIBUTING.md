# Contributing to reasoning-core

Thank you for your interest in contributing to reasoning-core! This document provides guidelines and instructions for contributing.

## 🚀 Quick Start

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Excelsior2026/reasoning-core.git
cd reasoning-core

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/reasoning_core --cov-report=html

# Run specific test file
pytest tests/test_concept_extractor.py -v

# Run tests matching pattern
pytest -k "medical"
```

### Code Quality

```bash
# Format code
black src tests
isort src tests

# Lint code
flake8 src tests

# Type check
mypy src

# Run all pre-commit hooks
pre-commit run --all-files
```

## 📝 Contribution Guidelines

### Code Style

- **Python**: Follow PEP 8
- **Line length**: 120 characters (enforced by black)
- **Imports**: Sorted with isort (black-compatible profile)
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Google style docstrings for all public APIs

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new domain plugin for legal reasoning
fix: correct relationship detection in medical domain
docs: update API documentation for knowledge graph
test: add edge case tests for concept extraction
refactor: simplify chain builder logic
```

### Pull Requests

1. **Create a feature branch**: `git checkout -b feature/amazing-feature`
2. **Make your changes**: Write code and tests
3. **Test thoroughly**: Ensure all tests pass
4. **Commit with clear messages**: Follow commit conventions
5. **Push to your fork**: `git push origin feature/amazing-feature`
6. **Open a PR**: Use the PR template

### PR Requirements

- ✅ All tests pass
- ✅ Coverage remains >= 80%
- ✅ Code is formatted (black, isort)
- ✅ No linting errors (flake8)
- ✅ Documentation updated (if applicable)
- ✅ CHANGELOG.md updated (for notable changes)

## 🎯 Areas for Contribution

### New Domain Plugins

We welcome domain plugins! Good candidates:

- **Legal**: Case law reasoning, precedent analysis
- **Engineering**: Technical documentation, architecture decisions
- **Education**: General pedagogy, learning patterns
- **Finance**: Investment analysis, risk assessment
- **Healthcare**: Nursing protocols, patient care workflows

**To add a domain:**

1. Create `src/reasoning_core/plugins/{domain}_domain.py`
2. Extend `BaseDomain` class
3. Implement all required methods
4. Add tests in `tests/test_{domain}_domain.py`
5. Update documentation

### Enhanced Extraction

- Improve concept extraction accuracy
- Add NER (Named Entity Recognition) integration
- Enhance relationship detection algorithms
- Better confidence scoring

### Graph Capabilities

- Visualization tools (D3.js, graphviz)
- Graph query language
- Subgraph pattern matching
- Graph similarity metrics

### Integration & Tools

- CLI tool for reasoning extraction
- Jupyter notebook extensions
- IDE plugins (VS Code, PyCharm)
- Export formats (GraphML, Cypher)

## 🧪 Testing Guidelines

### Test Structure

```python
class TestFeature:
    """Test feature description."""

    def test_basic_functionality(self):
        """Test basic use case."""
        # Arrange
        input_data = ...

        # Act
        result = function(input_data)

        # Assert
        assert result == expected

    def test_edge_case(self):
        """Test edge case."""
        with pytest.raises(ValueError):
            function(invalid_input)
```

### Test Coverage

- **Minimum**: 80% overall coverage (enforced by CI)
- **Target**: 90%+ for new code
- **Focus**: Edge cases, error handling, domain logic

### Test Types

1. **Unit tests**: Individual functions/methods
2. **Integration tests**: Component interactions
3. **Domain tests**: Domain-specific logic
4. **API tests**: High-level workflows

## 📚 Documentation

### Docstrings

Use Google style docstrings:

```python
def extract_concepts(text: str, domain: str = "generic") -> List[Concept]:
    """Extract concepts from text.

    Args:
        text: Input text to analyze.
        domain: Domain for specialized extraction.

    Returns:
        List of extracted Concept objects.

    Raises:
        ValueError: If text is None.

    Example:
        >>> extractor = ConceptExtractor()
        >>> concepts = extractor.extract("Medical text here")
        >>> len(concepts)
        5
    """
```

### README Updates

Update README.md when adding:
- New domains
- Major features
- Breaking changes
- New examples

## 🐛 Bug Reports

Use the bug report template and include:

- Clear description
- Reproduction steps
- Expected vs actual behavior
- Environment details
- Sample code/data (if applicable)

## 💡 Feature Requests

Use the feature request template and describe:

- Use case
- Proposed solution
- Domain impact
- Example usage

## 🤝 Code Review Process

1. **Automated checks**: CI must pass
2. **Maintainer review**: Code quality, design
3. **Feedback**: Address comments
4. **Approval**: Merge when approved

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors are recognized in:
- CHANGELOG.md
- GitHub contributors page
- Release notes

## 📞 Getting Help

- **Discussions**: GitHub Discussions for questions
- **Issues**: GitHub Issues for bugs and features
- **Email**: billparris@gmail.com for private inquiries

---

**Thank you for contributing to reasoning-core!** 🎉
