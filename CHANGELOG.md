# Changelog

All notable release-level changes are documented here. FairMind uses GitHub
prereleases while its public execution capabilities remain gated.

## [v2.1.0-alpha.1] - 2026-08-30

### Added

- P0 trustworthy control-plane evidence bindings, trust administration,
  review/decision separation, operational freshness, audit controls, and
  exact-run delegated separation-override grants.
- P0 dashboard state for evidence trust, freshness, and governance decisions.
- Explicit unavailable states for evaluation packs that are not independently
  validated or released.
- A Docs Forge-generated P0 guide set covering setup, workflow, evidence trust,
  permissions, API integration, operations, limitations, and an applicability-
  first EU AI Act evidence crosswalk.

### Changed

- Documentation and release claims now describe an internal, default-off alpha
  rather than a generally available evaluation or compliance product.
- Public website claims now match the alpha boundary; placeholder analytics,
  unverified access-form collection, and inaccurate research metadata were
  removed.
- The public website build moved to a patched Astro 7 / Node 22.12 toolchain.
- The old frontend deployment workflow is now a manual build-only check; this
  prerelease does not claim a production deployment.
- Ordinary governance decisions remain compatible with migration-verification
  schemas before 013l; delegated overrides still require the complete 013l
  migration.

### Not included

- Isolated workers, real evaluator engines, modality packs, lifecycle
  assurance, compliance certification, automatic approval, and automatic
  enforcement.

See [the release notes](docs/releases/v2.1.0-alpha.1.md) for scope, gates, and
known limitations.
