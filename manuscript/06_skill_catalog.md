# Skill Catalog {#sec:catalog}

The published library lives at `skills/` in the repository, one package per page, organized by section — the same organization the discovery stage derived from the site's own URL architecture. Each package contains a validated `SKILL.md` (with frontmatter name, description, and effect annotation) and a `manifest.json` binding it to its source pages, retrieval timestamps, and content hashes. `skills/index.json` is the machine-readable discovery index for agent harnesses.

The complete catalog below is a bound token: it is generated from the published tree at bind time, so it always describes the repository as it actually is.

{{SKILL_CATALOG}}

Every skill names its source page in its body and manifest. The catalog's *Words* column counts the rendered body words of each skill; shells that could not be augmented appear as the thinnest rows, with their failure receipts recorded in the augmentation analysis rather than hidden.
