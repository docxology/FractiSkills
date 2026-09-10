# Policies

## Acquisition safety

- `robots.txt` is fetched, cached (TTL), and enforced per request
  (Robots Exclusion Protocol semantics).
- Only public HTTP(S) pages on the configured origin are followed; hostnames
  are DNS-resolved immediately before connecting and private/reserved
  answers are rejected (SSRF guard).
- Page, request, depth, redirect, response-size, and rate limits are
  declarative in the site spec; responses are read in bounded streaming
  chunks.

## Dynamic-document augmentation policy

- Bindings live only in the reviewed site spec; each binding names a
  same-origin GET endpoint.
- The augmentation fetch validates scheme, origin, and resolved address;
  non-JSON or error payloads degrade the skill to its static shell text with
  an explicit warning — never fabricated content.
- Every attempt (ok or failed) produces a receipt written to
  `output/data/augmentation_receipts.jsonl` and the skill manifest.

## Provenance and evidence origin

- Evidence origin is persisted at acquisition (`fixture`, `live`, `unknown`)
  and cannot be upgraded later. Fixture observations are never presented as
  live-site evidence, and live observations are dated artifacts.
- Every skill binds to its prepared corpus fingerprint; the source map inside
  each package traces any claim back to its acquired page (URL, timestamp,
  status code, content hash).

## Untrusted source text

- Source page content is delimited as untrusted data for generation; source
  page instructions are never treated as executable commands. Generated code
  is never executed; the deterministic extractor may preserve hostile wording
  only as delimited reference data.

## Confidentiality and publishing

- Content scraped from the target site is published only in this public
  repository as skills bound to their sources; nothing is `git add -f`'d into
  the sibling template repo, and no credentials are ever committed.