# scripts/ — thin wrappers only

Each numbered script dispatches one `fractiskills` CLI stage and forwards its
arguments. Business logic lives in `src/fractiskills/`.

| Script | Stage |
| --- | --- |
| `00_preflight.py` | spec load + output writability check |
| `10_discover.py` | sitemap + bounded BFS crawl inventory |
| `20_render_skills.py` | one SKILL.md per discovered page |
| `30_publish_skills.py` | validate + publish tracked tree |
| `40_analyze.py` | aggregate artifacts |
| `50_figures.py` | visualizations |
| `60_validate.py` | validate tracked skill packages |
| `z_generate_manuscript_variables.py` | parent-template pre-render hook (ordered research build) |
