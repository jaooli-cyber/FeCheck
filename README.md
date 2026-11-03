# FeCheck

FeCheck is a deterministic property-testing, replay, and counterexample-shrinking
toolkit written in Fe for the Fe Builders Challenge.

The implemented vertical remains deliberately pure: a certified `u256` range
runner is now joined by the first canonical `ActionSeq<u256, N>` kernel. Stateful
EVM model testing is not claimed yet.

## What works now

- explicit pass, discard, fail, infrastructure, and configuration outcomes;
- byte-exact, length-prefixed V1 fingerprints with tagged fields;
- deterministic attempt identity from master seed, attempt index, and generation
  fingerprint;
- deduplicated edges that do not consume RNG;
- a generic `Strategy` contract with tested `U256Range` and `BoolStrategy`
  primitives;
- unbiased bounded generation with a hard, versioned rejection cap;
- certified `u256` replay capsules that regenerate one attempt without executing
  its prefix and verify the complete recorded shrink evidence;
- deterministic scalar shrinking with failure-key preservation and exact
  complete-vs-partial budget semantics;
- a type-enforced, effect-free `PureU256Property` certification boundary;
- a canonical, deliberately bounded `ActionSeq<u256, N>` kernel with private
  physical tail, capacity/max-action/action-strategy binding, deterministic edge
  and random generation, contiguous-block deletion, left-to-right argument
  shrinking, exact logical deduplication, and structural rank comparison;
- an effect-free pure ActionSeq runner with stable `FailureKey`, phase-A restart
  after acceptance, exact complete/partial budgets, and scalar-compatible
  accounting;
- independent PyCryptodome goldens for canonical preimages plus mutation tests
  for every scalar strategy and run fingerprint field.

The suite currently contains 66 passing Fe tests. The sequence tests include all
small values in `0..2` at every logical length through three, comparison against
an independent reference enumerator, exact shrink order and deduplication,
private-tail independence, capacities zero through the deliberately supported
maximum of four, termination after all 1,038 worst-case candidates, RNG
consumption across every physical slot, and canonical assertions backed by 25
independent Python vectors, including the sequence run fingerprint.

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
- `src/capsule.fe`: certified scalar run reports and fresh capsule replay.
- `src/scalar.fe`: deterministic scalar shrink cursor.
- `src/pure_runner.fe`: pure scalar runner, budgets, accounting, and shrinking.
- `src/action_seq.fe`: canonical bounded-u256 sequence kernel and retained V0
  non-wire spike.
- `src/action_seq_runner.fe`: pure sequence runner and fixed-point shrinking.
- `src/action_seq_tests.fe` and `src/action_seq_runner_tests.fe`: exhaustive
  kernel evidence plus runner budgets, accounting, and failure classification.
- `tools/oracle_vectors.py`: independent canonical-preimage oracle.
- `docs/SEMANTICS.md`: normative behavior implemented by the current slice.

## Status and limitations

This is an active contest build, not a finished submission. The scalar runner
and certified replay path are verified. The canonical sequence kernel and its
pure `FailureKey`-preserving runner are implemented, but sequence capsules and
direct sequence replay are not yet implemented. Stateful EVM fixtures,
fresh-per-candidate model execution, deployment salts, measured state/deployment
limits, external capsule serialization/decoding, and the final demo remain in
development. Gate C is therefore partial and is not represented as complete.

See [PROVENANCE.md](PROVENANCE.md) for the contest boundary, prior-work
disclosure, starter reuse, and AI-assistance statement.

## License

Apache License 2.0.
