# Fe Builders Challenge submission

The implementation, demo, documentation, Red Team review, and automated
verification for the contest scope are complete. The immutable submission
artifact is identified by the `v0.1.0` release tag. Its exact SHA, publication
date, and official receipt are recorded by GitHub and the private submission
records rather than asserted by this source tree.

- Project: FeCheck
- Repository: https://github.com/jaooli-cyber/FeCheck
- License: Apache-2.0
- Language/toolchain: Fe 26.5.0 (`3dab95f`), Sonatina, test profile, O1
- Status: implementation and verification complete
- Submission release: `v0.1.0`
- Registration/project identifiers: retained only in official private records

## Summary

FeCheck brings deterministic property testing, direct replay, and
failure-preserving shrinking to Fe. Its type-enforced pure scalar and bounded
`ActionSeq<u256, N>` boundaries produce certified capsules that commit the
failing attempt identity and verify exact shrink evidence.

For EVM state machines, FeCheck adds an explicitly non-certified,
manifest-bound layer. It separates semantic and execution identity, binds every
receipt to its exact candidate and fixture evidence, serializes a canonical
36-word stateful capsule, and performs a full-run recheck through the historical
attempt and shrink path under a fresh execution identity and distinct fixture
addresses in the same outer EVM. The generic callback remains a documented
trust boundary.

The AccountingLedger demonstration specializes that layer without accepting a
caller-selected identity or evaluator. A curated seed exposes a self-transfer
aliasing defect:

```text
original  [2,17,25] = Deposit(A,2), Transfer(A,A,1), Transfer(A,B,1)
minimal   [1,17]    = Deposit(A,1), Transfer(A,A,1)
```

The buggy run records 22 property/fixture evaluations, 66 deployments, and 21
executed actions. Its complete local shrink has 18 evaluations, 2 accepted
candidates, 8 rejected passes, 8 rejected discards, and no other failure key.
The corrected target passes the same seed and strategy. Replay uses distinct
fixture addresses and exactly reproduces the recorded `RunStats`, `ShrinkStats`,
shrink state, `FailureKey`, and original/reduced candidate digests.

## Claim boundary

- Pure scalar and sequence capsules use effect-free certification boundaries.
- Generic stateful receipt bindings are verified against the expected manifest
  and exact request; callback effects remain trusted and are neither proven
  truthful nor certified by Fe's type system.
- The stateful digest provides unauthenticated self-consistency, not signature,
  authorship, or authority.
- The AccountingLedger wrapper fixes the expected adapter, checks target and
  proxy runtimes before actions, and binds actual proxy initcode hashes.
- The reduced witness is a local minimum under the current shrink order, not a
  proof of global minimality or production security.

## Verification

The commands below assume that the pinned Fe 26.5.0 executable is available on
`PATH`.

```sh
fe --version
fe fmt --check
fe fmt --check tests/evm-probes
fe fmt --check tests/stateful-runner
fe fmt --check tests/accounting-ledger
fe fmt --check examples/quickstart
fe check . --profile dev
fe check tests/evm-probes --profile dev
fe check tests/stateful-runner --profile dev
fe check tests/accounting-ledger --profile dev
fe check examples/quickstart --profile dev
fe test . --backend sonatina --profile test -O 1 --jobs 1
fe test tests/evm-probes --backend sonatina --profile test -O 1 --jobs 1
fe test tests/stateful-runner --backend sonatina --profile test -O 1 --jobs 1
fe test tests/accounting-ledger --backend sonatina --profile test -O 1 --jobs 1
fe test examples/quickstart --backend sonatina --profile test -O 1 --jobs 1

python3 -m venv .venv-oracle
. .venv-oracle/bin/activate
python -m pip install -r tools/requirements-oracle.txt
python -m unittest tools/test_adapter_manifest.py
python tools/adapter_manifest.py \
  --check \
  --fe "$(command -v fe)" \
  --backend sonatina \
  --profile test \
  --opt 1
python tools/oracle_vectors.py
```

Current evidence totals:

- 108 root Fe tests;
- 9 EVM probe tests;
- 2 isolated stateful-runner tests;
- 15 AccountingLedger tests;
- 1 independent quickstart-consumer test;
- 135 passing Fe tests in total;
- 11 manifest-verifier unit tests;
- 32 core and 25 AccountingLedger oracle vectors.

## Verified release evidence

- implementation and flagship demo complete;
- Red Team final review: S0=0, S1=0, S2=0;
- pinned CI, source/toolchain manifest, and independent oracle green;
- provenance and Apache-2.0 license present.

The GitHub Release records the immutable tag, exact SHA, and publication date.
The official form and private submission records retain the receipt, project
identifier, and any private code; those values do not belong in this
repository.

See `README.md`, `docs/SEMANTICS.md`, `docs/STATEFUL_RUNNER.md`,
`docs/ACCOUNTING_LEDGER.md`, and `PROVENANCE.md` for the complete semantics,
evidence, limitations, and disclosure.
