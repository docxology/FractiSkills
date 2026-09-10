# Introduction {#sec:introduction}

Agent harnesses such as Codex, Claude Code, and Hermes load skills as portable `SKILL.md` packages: frontmatter plus structured Markdown that teaches an agent what a body of knowledge is, when to use it, and how to verify claims against sources. [Skillarum](@skillarum) renders such packages from *selected* public website pages. FractiSkills asks the natural next question: what does it look like to skill an **entire website** — every page, organized the way the site itself is organized, published as one reviewable artifact?

The subject is the *SS Vibelandia Omniversal Canvas* at {{BASE_URL}} — a self-described "digital Burning Man camp and art exhibit" built by a human host in Downtown Reno, openly published, with a `robots.txt` that explicitly welcomes all crawlers and a sitemap that enumerates the work. The site is a demanding test case for whole-site skilling precisely because it is not a static brochure: it mixes long-form static pages with client-rendered readers, JSON-backed catalogs, redirect stubs, and query-parameterized document routes.

This manuscript documents the FractiSkills pipeline (§\ref{sec:methods}), reports what one full live run produced (§\ref{sec:results}), presents the visual evidence (§\ref{sec:visualizations}), catalogs every generated skill in render order (§\ref{sec:catalog}), and states the limitations and boundaries honestly (§\ref{sec:discussion}). All numbers in the prose are manuscript tokens bound from persisted artifacts — none are hand-typed.

## Contributions {#sec:contributions}

1. **Whole-site skill coverage.** A discovery stage that unions the declared sitemap with a bounded breadth-first crawl, resolves redirect aliases to canonical pages, and partitions every page into the site's own section architecture — producing one target per page for the render stage.
2. **Declared dynamic-content augmentation.** An `AugmentedGenerator` that keeps Skillarum's deterministic skill body but retrieves client-rendered documents from reviewed, same-origin JSON endpoints, with per-fetch receipts recorded in skill metadata and run artifacts. Failures degrade to honest thin skills, never fabricated content.
3. **A tracked, reconciled skill library.** Validated packages published into a clean-cut `skills/` tree with a discovery index, plus analysis figures and a fully token-hydrated manuscript, all reproducible from a clean checkout.
