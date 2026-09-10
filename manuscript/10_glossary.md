# Glossary {#sec:glossary}

Agent harness — Runtime that loads a skill for a model: discovers `SKILL.md`, progressively discloses the body, invokes referenced tools.

SKILL.md — Single validated Markdown file Skillarum emits per target: YAML frontmatter plus a body whose *Semantic knowledge* section quotes the source page as untrusted data.

Skillarum — Pinned acquisition-and-generation engine; its five-stage pipeline (acquire → prepare → process → parse → render) turns a declarative YAML profile into skill packages.

FractiSkills — Project layer over Skillarum adding whole-site discovery, dynamic-content augmentation, and publication-scale organization.

Source profile — Declarative YAML defining a base URL, safety-bounded crawl configuration, extraction rules, and named targets; one profile per site section.

Target — Named profile entry mapping to exactly one page URL; the unit of acquisition and rendering.

Discovery union — Declared sitemap unioned with a bounded breadth-first crawl: one target per page after alias resolution and partitioning.

Redirect alias — URL resolving to another page's canonical location; recorded as an alias, not distinct content.

Canonical duplicate — Alias page consolidated onto its canonical URL so each page appears exactly once in the corpus.

BFS depth — A page's hop count from the base URL in the breadth-first crawl, capped by discovery configuration.

Section — Top-level partition of the site's URL architecture; each gets one compiled profile and one render run.

AugmentedGenerator — FractiSkills' subclass of the deterministic generator that, for URL-matched bindings, fetches a same-origin JSON endpoint and splices retrieved text into an otherwise deterministic skill body.

Augmentation receipt — Per-fetch provenance in metadata and run artifacts: endpoint, timestamp, HTTP status, content SHA-256, ETag, evidence origin.

Prepared corpus fingerprint — Content hash binding every rendered skill to its exact prepared corpus, enabling byte-identical reproduction.

Evidence origin — Manifest field classifying corpus text; here all evidence is live, fetched within the observation window rather than replayed from cache.

Discovery index — Published per-skill index linking each skill to its source URL, section, and provenance.

Effect annotation — Figure or prose note stating what augmentation changed relative to static acquisition, kept separate from raw measurements.

Reconciliation — Final consistency pass over manifests, hashes, counts, and tokens; manuscript, figures, and skill library must agree on one set of numbers.

Token binding — Rule that every manuscript number originates from a run artifact via a token placeholder; prose never hardcodes token-covered values.

Okabe-Ito palette — Colorblind-safe categorical palette used for all analysis figures.
