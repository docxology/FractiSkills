# Run the offline checks and render a fixture manuscript

The project uses Python 3.15 and uv. Install from the lockfile and run the
local tests. These tests use a benign synthetic site served on loopback.

```sh
uv sync --locked --extra dev
uv run python scripts/00_preflight.py
uv run pytest tests/ -m 'not live' --cov=src --cov-fail-under=90
uv run ruff check src tests scripts
```

The project does not execute any generated skill. The published live results
and their original limits are in the [archive evidence note](release_evidence.md).

## Pinned Template render

Install Python 3.14 for the Template runner, Pandoc 3.14, matching
pandoc-crossref v0.3.26b, and XeLaTeX with the
[Template TeX packages](https://github.com/docxology/template/blob/87704feae0a4490ef7dad9c931d268e8c30273c2/README.md#L565-L574).
Set `FRACTISKILLS_CHECKOUT` to the absolute path of this checkout and create
a disposable registered copy.

```sh
git clone https://github.com/docxology/template.git fractiskills-template-runner
cd fractiskills-template-runner
git checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
uv sync --locked --python 3.14
project=projects/working/FractiSkills
mkdir -p projects/working
git -C "$FRACTISKILLS_CHECKOUT" worktree add --detach "$PWD/$project" HEAD
(cd "$project" && uv sync --locked --extra dev --python 3.15)
"$project/.venv/bin/python" "$project/tests/prepare_manuscript_fixture.py"
uv run --no-sync python scripts/pipeline/stage_03_render.py --project working/FractiSkills
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project working/FractiSkills
```

The fixture script requires an empty output location and writes its packages
under `output/fixture-skills/`. Stage 03 builds the research artifacts and
binds the authored sections. The abstract labels this output as fixture
verification. The [archived live survey](release_evidence.md) remains the source
for the published live numbers.

The combined PDF is `$project/output/pdf/FractiSkills_combined.pdf` and the
HTML is `$project/output/web/index.html`. The manuscript binding receipt is
under `output/data/` and Template's validation and provenance live under
`output/reports/`. From the registered copy, check local links after
generating the figures:

```sh
(cd "$project" && lychee --offline README.md AGENTS.md 'docs/**/*.md')
git -C "$project" diff --check
```
