# Operations

The [local verification guide](quickstart.md) exercises the same stage
contracts with a benign synthetic site. The [source policy](policies.md)
defines the requirements for a separately authorized live observation.

## Configuration and artifacts

The reviewed [site specification](../data/sources/ssvibelandia.yaml) declares
the origin, sitemap, acquisition budgets, and same-origin bindings. The package
stage commands accept an alternate spec and output directory. Use their
`--help` output for exact options. The
[manuscript configuration](manuscript/config.yaml) supplies paper metadata,
publication identifiers, and render formats.

| Stage | Output |
| --- | --- |
| Discovery | `output/data/inventory.json`, including aliases and sitemap/crawl provenance |
| Rendering | `output/skills/`, run manifests, and augmentation receipts |
| Publication | Validated packages and an index under the selected skills directory, plus a publish receipt |
| Research | `output/data/fractiskills_analysis.json`, `skills.csv`, figure registry, variables, and manuscript receipt |
| Template | `output/manuscript/`, generated figures, combined PDF and HTML, and validation reports |

Fixture publication uses `output/fixture-skills/`. A project-native CLI
invocation can set a different skills directory explicitly. The default
tracked `skills/` tree belongs to the published corpus.

## Recovery

Keep inventory, render summary, receipts, and skill packages from the same
run. The offline research step reads these persisted inputs. Check
`output/data/render_summary.json` for failed sections and the corresponding
`output/runs/<run-id>/failure.json` for diagnostics. An incomplete run can be
investigated before performing any publication reconciliation.

Retain old observation receipts independently of a fresh run. The archived
[version evidence](release_evidence.md) documents which inputs are publicly
available for the existing release. A local fixture run cannot regenerate
the original live observation.
