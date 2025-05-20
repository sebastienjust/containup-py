# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.10] - unreleased

### Changed

- Changed odoo example to n8n example to be able to demonstrate more things.

## [0.1.9] - 2025-05-19

### Added

- Labels support

### Fixed

- Fully functionnal example with PostgreSQL + Odoo + Traefik + PGAdmin.

## [0.1.8] - 2025-05-18

### Fixed

- display Docker errors in logs

## [0.1.7] - 2025-05-18

### Added

- Real healthchecks
- depends_on fully functionnal and really depending on healthchecks.
- improved reporting on healthchecks and depends_on.
- issue warning if depends_on points to a service without healthcheck.

### Fixed

- Installer script to test the features was not pushed.
- Bad dependency on typings_extensions.

### Documentation

- Improved Readme and better wording.

## [0.1.6] - 2025-05-16

### Breaking changes

- Port syntax improved (Fixes #18)

### Added

- Dry-run feature: previsualize how the stack will be built. Generates a report on stdio (console output).
- Secrets management: you can secure your secrets while building the stack (Fixes #41)
- Extendable plugin registry: you can add your own plugins
- Extension point for audits: bring your own stack audits

### Fixed

- Bad command line extra-arguments parsing

### Documentation

- Installed Sphinx and create documentation project
- Install Furo as HTML template
- Added documentation : How to parse command line extra arguments
- Added documentation : How to manage container inter-dependencies
- Added documentation : How to manage container scaling

## [0.1.5] - 2025-05-13

- Just some more documentation and links to get feedback on the tool.

## [0.1.4] - 2025-05-13

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
