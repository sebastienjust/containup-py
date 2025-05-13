# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2025-03-13 

### Changed

- No more need to pass `config` as argument to `containup_run`.
- No more need to use `containup_cli()` at the beginning of the script, unless you have special needs to read
  your own command-line arguments.
- Enforce integer-only durations and cap maximum duration to 1 week in `duration_to_nano`. Fixes #2 
  It means that health check timers cannot have intervals longer than one week.
- More default parameters for mounts (volumes), health and networks.
  It means you can write less code.

### Internal

- More separation between business logic and infrastructure. I tend to go towards a full hexagonal architecture.

  The goal is to be able to operate Podman later. 
  It also means we can get unit tests on workflows.

- No more sys.exit() inside business logic (it was not testable anyway)

  Using ports/adapters for side effects.
  Even if it's not finished, it's a good start.

### Infrastructure

- Check (lint, test, build) on all Pull Requests. Fixes #1
- Cleanup code in publication workflow. Fixes #1
- Improved PR Management. Fixes #1

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