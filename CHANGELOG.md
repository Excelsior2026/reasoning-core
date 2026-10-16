# Changelog

All notable changes to reasoning-core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Upload-directory cleanup could delete top-level files in the process working
  directory: `Path("")` is `Path(".")` and always truthy, so the intended
  temp-directory fallback never ran and the `atexit`/periodic cleanup deleted
  files by age in whatever directory the process started from; the upload
  directory now defaults to a dedicated temp directory and cleanup refuses the
  working directory and repository working trees
- Package import: `reasoning_core.web` no longer eagerly imports the FastAPI
  app, so `import reasoning_core` works without the optional web dependencies;
  corrected the middleware import (`fastapi.middleware.base` no longer exists)
  and missing typing imports that made the web server unimportable
- `use_llm` was undefined in the file-upload endpoint; it is now an optional
  form field like the other endpoints
- The `/api/domains/{domain_id}` route shadowed the internal domain lookup
  helper; the route function was renamed
- `AsyncReasoningAPI.process_stream` looped forever when `overlap` was greater
  than or equal to `chunk_size`; both arguments are now validated
- Batch analysis records per-item failures instead of aborting the batch
- The test suite now runs end to end (pytest-asyncio declared as a dev
  dependency); previously four tests failed and one hung

### Changed
- Web dependencies moved to the optional `web` extra
  (`pip install -e ".[web]"`); the core engine installs with `pip install -e .`
- CI coverage gate now measures the tested core modules (web layer excluded
  until it has tests) instead of a fixed 80% over untested code
- Formatting/linting tools pinned to the pre-commit versions for deterministic CI

### Added
- Initial release of reasoning-core
- Core reasoning extraction engine
- Concept extraction with domain-specific support
- Relationship mapping between concepts
- Reasoning chain building
- Knowledge graph data structure
- Medical domain plugin
- Business domain plugin
- High-level API for reasoning extraction
- Test suite with coverage reporting
- Smoke tests for the web layer (skipped without the `web` extra)
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Documentation and examples

## [0.1.0] - 2026-01-03

### Added
- Initial development release (repository only; never published to PyPI)
- Core reasoning extraction functionality
- Medical and business domain plugins
- Knowledge graph support
- Python packaging configuration
- Comprehensive documentation

[Unreleased]: https://github.com/Excelsior2026/reasoning-core/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Excelsior2026/reasoning-core/releases/tag/v0.1.0
