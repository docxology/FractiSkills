# Skill Catalog {#sec:catalog}

The published library lives at `skills/` in the repository, one package per page, organized by section — the same organization the discovery stage derived from the site's own URL architecture. Each package contains a validated `SKILL.md` (frontmatter name, description, effect annotation) and a `manifest.json` binding it to its source pages, retrieval timestamps, and content hashes.

`skills/index.json` is the machine-readable entry point for consumer harnesses. Its top-level `schema_version` gates parsing: a harness rejects or migrates on mismatch before touching anything else. The `skills` array carries one record per package, each naming its `area` (the section), its `path` (repository-relative `SKILL.md` location), and the resolved skill name — enough for a loader to enumerate, filter by area, and read packages without re-deriving layout conventions. Package directory names are path-derived from the source URL and therefore stable across regenerations; human-facing titles drift, so consumers should key on paths and names, never on titles.

The complete catalog below is a bound token: generated from the published tree at bind time, it always describes the repository as it actually is.

{{SKILL_CATALOG}}

Every skill names its source page in its body and manifest. The catalog's *Words* column counts the rendered body words of each skill. The thinnest rows are not padding defects: they correspond to honest failures — sources whose augmentation returned an error or empty payload — and each ships with a failure receipt (API URL, error class, timestamp) in the augmentation analysis rather than a silently hollowed skill.
