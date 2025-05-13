# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] 

- Nothing

## [0.1.3] - 2025-05-13

### Documentation

- More accurate [README.md](README.md)

### Infrastructure

- added hyperlinks in [pyproject.toml](pyproject.toml) for better discovery
- Renamed GitHub workflow


## [0.1.2] - 2025-05-13

### Infrastructure

- First publication on PyPI using GitHub workflows

## [0.1.1] - 2025-05-13

### Infrastructure

- Integration with GitHub workflows

## [0.1.1] - 2025-05-12

### Infrastructure

- Prepared for first PyPI release: updated metadata, added classifiers and keywords.
- Added changelog and project automation scripts.

## [0.1.0] - 2025-05-12

This is a first public version, still experimental. The API and CLI are subject to change.

Contributions and issues are temporarily limited until the base is stable.

### Added

- Initial release of `containup`.
- Define and run Docker Compose-like stacks entirely in Python.
- Support for declaring services, volumes, networks with native Python code.
- First usable CLI with support for `up`, `down`, `logs`, and service selection.
- Extensible logic: supports conditions, secrets, loops, and dynamic configuration.
- Strong typing and IDE support (autocompletion, static checks).
- Basic example stack included in README.
- Development toolchain with `pytest`, `ruff`, `black`, `pyright`.

---

Categories: Added, Changed, Deprecated, Removed, Fixed, Security, Documentation, Infrastructure