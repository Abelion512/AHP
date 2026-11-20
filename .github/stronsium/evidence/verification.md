# Proof repair verification and rollout boundary

## What this branch changes

The proof producer, context collector and verifier library use `Abelion512/Stellarium` while retaining the same immutable repository/owner/bot ids. The producer reports a fixed `not_applicable` result for known scope exclusions and emits no positive proof artifact. A completed job is not a positive proof.

The same-repository-head, draft exclusion and 30-file limit already existed in `producer_context.py`. This repair does not newly exclude drafts or increase the limit. Preflight imports the collector's `MAX_PROOF_FILES`; a regression checks the existing draft refusal. Preflight may read an earlier PR snapshot, but `run()` independently re-collects the context and rejects changed head/base/reviews before and after proof production. A stale preflight can refuse unnecessarily or fail later, never prove a newer snapshot.

## Tests actually run

`python3 -m pytest -q producer_test.py proof_test.py p4_semantic_test.py review_boundary_test.py run_producer_test.py producer_flow_test.py` in `.github/stronsium`: 103 tests and 154 subtests passed locally on Python 3.12. CI (`.github/workflows/stronsium-proof-tests.yml`) runs `python3 -B -m unittest discover -p "*_test.py" -v`, which selects the same six files. The original branch head also passed the repository producer-unit workflow configured for Python 3.14. The revised head needs its own fresh CI result.

The registered callables are now checked against the code the verified file defines (`trusted_program_mismatch`), so a miswired wiring entry cannot run an unrelated check under an approved definition digest.

`MissingArtifactBoundary` exercises the repository's real `SelectedArtifactProof` adapter: absent/invalid artifact id cannot create a proof source, a GitHub artifact 404 raises instead of returning a receipt, and neither `None` nor a successful job-shaped dictionary passes `receipt_matches`. These are repository-library tests with injected transport failure, not a live deployed-consumer test.

## Exact rollout boundary

Available source in this repository:

- `github_proof_transport.py`: `SelectedArtifactProof` accepts explicit run/attempt/artifact ids and downloads an artifact before invoking the verifier. It does not discover or select artifacts based on CI success.
- `proof_evidence.py`: `ProofVerifier` verifies artifact/run provenance, content digest, context, closure and definitions. `ProducerPolicy` is supplied by its caller. A receipt still grants no approval or merge authority.
- `producer_identity.py`: producer-side policy is derived from the default-branch checkout. This is not evidence of the deployed consumer's configuration.

The deployed consumer source, actual installed repository-name constant, artifact-selection behavior and closure-pin configuration have NOT been located or inspected. This PR cannot assert that the live consumer denies a missing artifact, uses this adapter, or is ready for the new repository name. Do not substitute the offline adapter test for that missing deployment check.

Changing any closure member changes the expected content digest. Keep existing consumer pins unchanged until separately reviewed rollout work establishes their actual location and configuration. A live rollout must verify the deployed consumer's canonical AHP identity, missing-artifact denial and new reviewed closure pin together. Then an eligible same-repository Python-AST-only PR must prove positive verification and an out-of-scope PR must prove no approval. No live pin edit, owner-acceptance toggle, deployment or merge was performed here.

`OBSERVATIONAL_SCOPE_OWNER_ACCEPTED` remains `False`. This repair is not autonomous-approval readiness. The default-branch proof may remain red while the repair PR is unmerged because `pull_request_target` executes the main-branch producer.
