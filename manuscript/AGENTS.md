# manuscript/ — token-bound manuscript sources

- Numbered chapters (`00_abstract.md` … `99_references.md`) are pristine
  sources; `{{TOKEN}}` placeholders resolve only into `output/manuscript/`.
- Numeric prose uses bound tokens exclusively (`TOTAL_PAGES`, `SKILL_COUNT`,
  `SECTION_TABLE`, `SKILL_CATALOG`, figure captions, …). Unknown tokens fail
  the bind loudly.
- `config.yaml` carries paper metadata consumed by the parent renderer;
  `references.bib` uses natbib keys cited as `[@key]`.
- `layer_contract.yaml` documents the enforced surface rules.
- Figures are referenced as `../output/figures/<name>.png` with registry
  captions (`FIGURE_<ID>_CAPTION` tokens).
