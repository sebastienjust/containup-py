# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-05-12

### Added

- Initial release of `containup`.
- Define and run Docker Compose-like stacks entirely in Python.
- Support for declaring services, volumes, networks with native Python code.
- First usable CLI with support for `up`, `down`, `logs`, and service selection.
- Extensible logic: supports conditions, secrets, loops, and dynamic configuration.
- Strong typing and IDE support (autocompletion, static checks).
- Basic example stack included in README.
- Development toolchain with `pytest`, `ruff`, `black`, `pyright`.

### Notes

- This is a first public version, still experimental.
- The API and CLI are subject to change.
- Contributions and issues are temporarily limited until the base is stable.
