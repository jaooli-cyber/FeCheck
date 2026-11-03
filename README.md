# FeCheck

FeCheck is a deterministic property-testing, replay, and counterexample-shrinking
toolkit written in Fe for the Fe Builders Challenge.

The executable runner vertical remains deliberately pure: certified `u256`
range and canonical `ActionSeq<u256, N>` runners produce directly replayable
failure capsules. A separate stateful identity and budget-admission foundation
now exists, but stateful EVM model testing is not claimed yet.

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
- a distinct typed ActionSeq capsule and direct replay path that bind capacity,
  maximum length, action strategy, codec, run configuration, attempt identity,
  canonical dynamic value digests, and exact shrink evidence without executing
  the attempt prefix;
- canonical V1 fixture salts binding run identity, seed, attempt, local
  evaluation, and stable Target/ActorA/ActorB role tags;
- an ingot-internal state/deployment preflight plus a bounded caller-owned
  duplicate registry, explicitly not presented as a certified stateful API, an
  EVM-global registry, a persistent deployment reservation, or an EVM fixture
  runner;
- independent PyCryptodome goldens for canonical preimages plus mutation tests
  for every scalar strategy and run fingerprint field.

The suite currently contains 85 passing Fe tests. The sequence tests include all
small values in `0..2` at every logical length through three, comparison against
an independent reference enumerator, exact shrink order and deduplication,
private-tail independence, capacities zero through the deliberately supported
maximum of four, termination after all 1,038 worst-case candidates, RNG
consumption across every physical slot, and canonical assertions backed by 32
independent Python vectors, including the sequence run fingerprint, a non-edge
attempt at index four through its complete RNG chain and value digest, and the
754-byte fixture-salt preimage.

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
- `src/action_seq_capsule.fe`: certified sequence reports, typed capsules, and
  direct sequence replay.
- `src/stateful.fe`: stateful fixture identity, fixed deployment-plan
  validation, atomic admission, and a caller-owned run registry.
- `src/action_seq_tests.fe`, `src/action_seq_runner_tests.fe`,
  `src/action_seq_capsule_tests.fe`, `src/fixture_identity_tests.fe`, and
  `src/stateful_tests.fe`: kernel, runner, capsule, canonical salt, budget,
  registry, accounting, tamper, and failure-classification evidence.
- `tools/oracle_vectors.py`: independent canonical-preimage oracle.
- `docs/SEMANTICS.md`: normative behavior implemented by the current slice.

## Status and limitations

This is an active contest build, not a finished submission. The scalar and
canonical sequence kernels, pure `FailureKey`-preserving runners, certified
capsules, and direct replay paths are verified. Canonical deployment salts and
the pre-EVM state/deployment admission boundary are also verified. Actual
stateful EVM fixtures, fresh-per-candidate model execution, successful
deployment/action accounting, measured state/deployment limits, external
capsule serialization/decoding, and the final demo remain in development. Gate
C is therefore partial and is not represented as complete.

See [PROVENANCE.md](PROVENANCE.md) for the contest boundary, prior-work
disclosure, starter reuse, and AI-assistance statement.

## License

Apache License 2.0.
