# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-10-20

### Added
- `agrometrics report`: static HTML reliability report with key figures, timeline, downtime by cause and per-node table.
- Multi-stage `Dockerfile` (non-root runtime image) with a `serve` mode that publishes the demo report on port 8000.
- `Jenkinsfile` with lint, unit tests (JUnit), Docker build, smoke test, optional Docker Hub push and test-server deployment.
- Local Jenkins in `jenkins/` (Docker Compose, plugin list, Configuration as Code that creates the job).
- Kubernetes manifests in `k8s/` and `deploy/minikube.sh` for deployment to Minikube.
- Docker build and smoke test job in GitHub Actions.

## [0.1.0] - 2026-10-08

### Added
- Gap and outage detection per node from timestamped readings.
- Availability, MTBF, MTTR, data completeness and packet delivery ratio (from the LoRaWAN frame counter).
- Failure attribution to logged causes, with security events as one cause among others.
- Seeded simulator with ground-truth outages and a validation script.
- `agrometrics` command line with `simulate`, `summarize` and `plot`.
- Test suite (pytest, coverage gate 90%) and GitHub Actions pipeline with lint, test matrix, reproduction run, package build and tag-based release.

### Fixed
- Completeness no longer drops a slot when transmission jitter moves a reading across a slot boundary (readings are snapped to the nearest slot).
