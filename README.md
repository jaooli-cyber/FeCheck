# FeCheck

FeCheck is a deterministic property-testing, replay, and counterexample-shrinking
toolkit written in Fe for the Fe Builders Challenge.

The current vertical slice is deliberately pure and small: it proves the core
semantics with a `u256` range strategy before stateful EVM model testing is
introduced.

## What works now

- explicit pass, discard, fail, infrastructure, and configuration outcomes;
- byte-exact, length-prefixed V1 fingerprints with tagged fields;
- deterministic attempt identity from master seed, attempt index, and generation
  fingerprint;
- deduplicated range edges that do not consume RNG;
- a generic `Strategy` contract with tested `U256Range` and `BoolStrategy`
  primitives;
- unbiased bounded generation with a hard, versioned rejection cap;
- certified replay capsules that regenerate one attempt without executing its
  prefix, re-run shrinking, and verify the entire recorded shrink evidence,
  including counters and completion status;
- deterministic scalar shrinking with failure-key preservation;
- complete-vs-partial shrink budget semantics;
- a type-enforced, effect-free `PureU256Property` certification boundary;
- bounded `ActionSeq<A, N>` representation and a clearly non-wire digest spike;
- independent PyCryptodome golden vectors, exact preimage bytes, and mutation
  tests for every strategy and run fingerprint field.

The test suite currently contains 45 passing tests, including exhaustive scalar
strategy checks over all origin/value pairs in `0..15`, top-of-`u256` boundary
vectors, Bool strategy checks, capsule seed/index/statistics tampering, replay
result classification, a seeded random-attempt end-to-end replay, and
`PartialBudget` replay with a one-evaluation budget.

## Verify

FeCheck is pinned to Fe `26.5.0` (`3dab95f`).

```sh
fe --version
fe fmt --check .
fe check . --profile dev
fe test . --backend sonatina --profile test -O 1 --jobs 1
```

The project is currently a library and has no deployable contract, so
`fe build` is intentionally not part of CI yet.

The independent oracle also runs in CI but does not participate in the Fe
runtime:

```sh
python3 -m venv .venv-oracle
. .venv-oracle/bin/activate
python -m pip install -r tools/requirements-oracle.txt
python tools/oracle_vectors.py
```

CI locks its Linux x86-64 oracle wheel by SHA-256 in
`tools/requirements-oracle-ci.txt`.

## Layout

- `src/outcome.fe`: structured verdicts, outcomes, and statistics.
- `src/codec.fe`: byte-exact canonical preimages and Keccak fingerprints.
- `src/strategy.fe`: generic strategy contract and `U256Range`.
- `src/bool_strategy.fe`: Bool fingerprint, generation, digest, and shrinking.
- `src/replay.fe`: attempt identity, range edges, and direct regeneration.
- `src/capsule.fe`: certified run reports and fresh capsule replay.
- `src/scalar.fe`: deterministic scalar shrink cursor.
- `src/pure_runner.fe`: pure runner, budgets, accounting, and shrinking.
- `src/action_seq.fe`: bounded sequence and explicitly non-wire digest spike.
- `tools/oracle_vectors.py`: independent canonical-preimage oracle.
- `docs/SEMANTICS.md`: normative behavior implemented by the current slice.

## Status and limitations

This is an active contest build, not a finished submission. The pure `u256`
runner and its in-Fe certified replay path are verified. `BoolStrategy` is a
tested strategy primitive but is not yet wired into a certified Bool runner.
Stateful EVM fixtures, model-based action execution, canonical sequence
generation/shrinking, external capsule serialization/decoding, and the final
demo are still in development and are not claimed as complete.

See [PROVENANCE.md](PROVENANCE.md) for the contest boundary, prior-work
disclosure, starter reuse, and AI-assistance statement.

## License

Apache License 2.0.
