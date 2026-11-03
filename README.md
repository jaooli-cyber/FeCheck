# FeCheck

[![CI](https://github.com/jaooli-cyber/FeCheck/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jaooli-cyber/FeCheck/actions/workflows/ci.yml)

FeCheck is a deterministic property-testing, replay, and counterexample-shrinking
toolkit written in Fe for the Fe Builders Challenge.

The executable runner vertical remains deliberately pure: certified `u256`
range and canonical `ActionSeq<u256, N>` runners produce directly replayable
failure capsules. Alongside it, an explicitly experimental stateful
`ActionSeq<u256, N>` runner owns deterministic scheduling, fresh-evaluation
identity, budgets, counters, and failure-key-preserving shrinking for a fixed
three-contract fixture. Consumer-defined EVM callbacks remain a documented
trust boundary, so this path is not certified.

A separate manifest-bound layer emits a canonical stateful capsule and performs
a full-run recheck: it repeats the attempt prefix, failing attempt, and shrink
path under a distinct execution identity, then compares all recorded evidence
exactly. On a non-divergent prefix it executes attempts `0..attempt_index`; a
terminal earlier divergence stops there, and no path ever executes a later
attempt. This is verified replay, not certification of an arbitrary callback.

The AccountingLedger demonstration applies that boundary to a two-actor ledger,
exposes a self-transfer aliasing defect, and deterministically shrinks it to
`Deposit(A,1), Transfer(A,A,1)`. A corrected target is exercised with the same
generated workload. Its specialized wrapper fixes the adapter identity, observes
runtime code hashes, and exercises manifest-bound replay without claiming
type-level certification.

## Assurance at a glance

| Path | Boundary | Replay | Claim |
| --- | --- | --- | --- |
| Pure scalar and `ActionSeq` | Effect-free typed property | Direct failing attempt; no prefix execution | FeCheck-certified capsule |
| Experimental stateful scheduler | Consumer-defined callbacks | Structured run and shrink; no replay capsule | Scheduling and accounting verified; callback effects trusted |
| Manifest-bound stateful layer | Expected manifest and request-bound receipts | Full-run recheck under a new execution identity | Receipt binding verified; callback effects trusted; not type-certified |
| AccountingLedger | Fixed adapter and runtime manifest | Distinct fixture addresses in the same outer EVM | Specialized verified evidence; not type-certified |

“Certified” is FeCheck's term for its type-enforced, effect-free property
boundary. It is not a claim of external certification or a general formal proof
of contract correctness.

## Quick start

Prerequisite: Fe 26.5.0 (`3dab95f`) on `PATH`. These focused commands exercise
the smallest certified scalar flow and the complete AccountingLedger demo:

```sh
fe test . --backend sonatina --profile test -O 1 --jobs 1 \
  --filter certified_run_replays_without_executing_the_prefix

fe test tests/accounting-ledger --backend sonatina --profile test -O 1 --jobs 1
```

The flagship demo produces this deterministic evidence:

| Evidence | Result |
| --- | --- |
| Original | `[2,17,25]` = `Deposit(A,2), Transfer(A,A,1), Transfer(A,B,1)` |
| Local minimum | `[1,17]` = `Deposit(A,1), Transfer(A,A,1)` |
| Comparison | Buggy target falsifies; corrected target passes the same seed and strategy |
| Run accounting | 22 evaluations, 66 deployments, 21 executed actions |
| Shrink accounting | 18 evaluations, 2 accepted, 8 pass, 8 discard, 0 other-key |

A minimal independent consumer lives in
[`examples/quickstart`](examples/quickstart/src/lib.fe). Run it with:

```sh
fe test examples/quickstart --backend sonatina --profile test -O 1 --jobs 1
```

For a judge-oriented reading path, continue with the
[end-to-end ledger test](tests/accounting-ledger/src/lib.fe), the
[manifest-bound implementation](src/stateful_bound_recheck.fe), and the
[stateful claim boundary](docs/STATEFUL_RUNNER.md).

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
  duplicate registry, explicitly not presented as an EVM-global registry or a
  persistent deployment reservation;
- the public `check_u256_action_seq_stateful_experimental` scheduler, with a
  fixed Target/ActorA/ActorB deployment count of three, transactional registry
  adoption, deterministic original/shrink contexts, scheduler-side fixed
  deployment accounting, validated action receipts, and the same failure-key
  shrink discipline as the pure sequence runner;
- a manifest-bound stateful layer with separate semantic and execution
  identities, request-bound receipts, observed fixture evidence, a caller-owned
  replay registry, and an exact full-run recheck;
- a canonical stateful wire containing 35 payload words plus one self-excluded
  digest word: exactly 36 big-endian words / 1,152 bytes, with exact-length,
  version, flag, tag, capacity, and digest validation;
- adapter identity binding the protocol and fixture plan, concrete fixture
  policy, action/model/snapshot/failure schemas, adapter logic, target initcode,
  the actor initcode template at `Address::zero()`, runtime hashes, source
  bundle, and pinned toolchain/build profile;
- dynamic fixture evidence binding the adapter, the three deployed addresses,
  both actor initcode hashes instantiated with the actual target, and the three
  observed runtime code hashes into every callback receipt;
- a separate Fe 26.5.0 probe ingot covering exact CREATE2 prediction, a
  three-contract Target/ActorA/ActorB fixture, bound proxy callers, two isolated
  fixtures in one EVM, conservative occupied-address preflight, direct
  collision/constructor reverts, and outer-call failure capture;
- a separate stateful-runner ingot whose golden run performs eight fresh
  evaluations in one EVM, twenty-four direct typed CREATE2 deployments, eight
  actions through both bound actors, and a five-candidate shrink to length two;
- a separate AccountingLedger ingot with a packed action word, pure
  preview/commit model, bound ActorA/ActorB proxies, buggy and fixed targets,
  failure-key-stable invariant precedence, and a curated seed whose current
  shrink reaches the local witness `Deposit(A,1), Transfer(A,A,1)`, plus a
  specialized manifest-bound replay that uses fresh fixture addresses and
  reproduces all recorded counters exactly;
- independent PyCryptodome goldens for canonical preimages plus mutation tests
  for every scalar strategy and run fingerprint field, plus independent
  AccountingLedger fingerprints, RNG draws, model execution, shrink trace,
  counters, adapter identities, capsule wire, and execution identities;
- an independent eleven-test Python verifier for the AccountingLedger source
  bundle, pinned Fe binary, semantic domains, and declared
  backend/profile/optimization policy.

The root ingot contains 108 passing Fe tests, the isolated EVM capability ingot
contains 9, the isolated stateful-runner ingot contains 2, and the dedicated
AccountingLedger ingot contains 15. The independent quickstart adds one more,
for 135 passing Fe tests in total. The sequence tests include all small values in
`0..2` at every logical length through three, comparison against an independent
reference enumerator, exact shrink order and deduplication, private-tail
independence, capacities zero through the deliberately supported maximum of
four, termination after all 1,038 worst-case candidates, RNG consumption across
every physical slot, and canonical assertions backed by independent Python
vectors, including the sequence run fingerprint, a non-edge attempt at index
four through its complete RNG chain and value digest, and the 754-byte
fixture-salt preimage. The oracle verifies 32 core vectors plus 25
AccountingLedger vectors covering the packed domain, seed 1608 attempt, four
Keccak draws, exact shrink trace, corrected 8/8 rejection accounting, six exact
semantic domains, and bound replay identities.
Nine EVM probes separately verify the test-only deployment boundary. Two
additional EVM tests exercise the experimental runner and its direct CREATE2
revert boundary without extending the pure certified capsule APIs. The root
stateful tests additionally exercise manifest and receipt mismatch, exact raw
wire length, capsule self-consistency, replay-registry transactions, fresh
execution identity, and exact full-run evidence comparison.

## Verify

FeCheck is pinned to Fe `26.5.0` (`3dab95f`). On Linux x86-64, install the exact
binary used by CI and verify it before execution:

```sh
fecheck_tool_dir="$(mktemp -d)"
curl --proto '=https' --tlsv1.2 -fL --retry 3 \
  -o "$fecheck_tool_dir/fe" \
  https://github.com/argotorg/fe/releases/download/v26.5.0/fe_linux_amd64
printf '3732fbe8a6e9d2ea3925d02d0e3a1478bc1e01d742c2be75d3ea7300c46c45f0  %s\n' \
  "$fecheck_tool_dir/fe" | sha256sum -c -
chmod +x "$fecheck_tool_dir/fe"
export PATH="$fecheck_tool_dir:$PATH"
fe --version
```

Run the complete Fe suite:

```sh
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
```

The root ingot is a library with no deployable contract. CI runs `fe build`
against that root and fails if it emits any contract artifact. Deployable probe
contracts live only in the separate `tests/evm-probes` and
`tests/stateful-runner` ingots; AccountingLedger targets and proxies live only
in `tests/accounting-ledger`.

The independent oracle also runs in CI but does not participate in the Fe
runtime:

```sh
python3 -m venv .venv-oracle
. .venv-oracle/bin/activate
python -m pip install -r tools/requirements-oracle.txt
python tools/oracle_vectors.py
```

CI locks its Linux x86-64 oracle wheel by SHA-256 in
`tools/requirements-oracle-ci.txt`. It also runs the source/toolchain manifest
verifier with the exact Fe binary used for the test job:

```sh
python -m unittest tools/test_adapter_manifest.py
python tools/adapter_manifest.py \
  --check \
  --fe "$(command -v fe)" \
  --backend sonatina \
  --profile test \
  --opt 1
```

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
- `src/stateful_action_seq_runner.fe`: experimental stateful scheduler,
  effect-row callback boundary, stateful accounting, and shrinking.
- `src/stateful_bound_recheck.fe`: manifest-bound receipts, canonical stateful
  capsule/wire, replay registry, and exact full-run recheck; this is a verified
  boundary, not callback certification.
- `tests/evm-probes`: separate ingot containing CREATE2, bound-proxy,
  freshness, occupied-address, and revert-boundary evidence.
- `tests/stateful-runner`: separate ingot containing the full experimental
  scheduler golden and its direct-collision boundary.
- `tests/accounting-ledger`: separate demonstration ingot containing the packed
  action adapter, pure model, buggy/fixed ledger targets, bound proxies, and EVM
  evidence.
- `examples/quickstart`: independent consumer of the certified scalar API.
- `src/action_seq_tests.fe`, `src/action_seq_runner_tests.fe`,
  `src/action_seq_capsule_tests.fe`, `src/fixture_identity_tests.fe`, and
  `src/stateful_tests.fe` plus `src/stateful_action_seq_runner_tests.fe`:
  kernel, runner, capsule, canonical salt, budget, registry, accounting,
  callback-protocol, tamper, and failure-classification evidence.
- `tools/oracle_vectors.py`: independent canonical-preimage oracle.
- `tools/adapter_manifest.py`: independent AccountingLedger source/toolchain
  manifest verifier.
- `docs/SEMANTICS.md`: normative behavior implemented by the current slice.
- `docs/EVM_PROBES.md`: exact EVM evidence and its claim boundary.
- `docs/STATEFUL_RUNNER.md`: experimental scheduler protocol, evidence, and
  non-certification boundary.
- `docs/ACCOUNTING_LEDGER.md`: demo architecture, deterministic witness, shrink
  accounting, fixed comparison, and honest claim boundary.

## Status and limitations

Implementation and verification for the Fe Builders Challenge scope are
complete. The immutable submission artifact is identified by the `v0.1.0`
release tag. Repository publication, challenge acceptance, and external
submission status are recorded by GitHub and the official form rather than
asserted by this source tree.

The scalar and canonical sequence kernels, pure `FailureKey`-preserving
runners, certified capsules, and direct replay paths are verified. Canonical
deployment salts and the pre-EVM state/deployment admission boundary are
also verified. Test-only EVM probes verify exact deployments, bound callers,
same-EVM fixture isolation, and the direct CREATE2 revert boundary. The
experimental scheduler assigns fresh identities to every original and shrink
evaluation, enforces its budgets, and accounts for its fixed three-deployment
fixture and executed-action receipts. Its isolated golden exercises a fresh
fixture and local model on every candidate. AccountingLedger supplies a
concrete model-based consumer and fixed-target comparison with the same
generated sequence.

The manifest-bound layer completes the implemented full-run replay slice: its
identity binds the adapter, policies, code hashes, source bundle, and pinned
build; its wire is externally serializable and length-exact; and replay repeats
the complete deterministic run under fresh salts before accepting exact
evidence. AccountingLedger specializes that boundary and checks all three
runtime code hashes before bindings, initial state, or actions.

This still does not make the generic stateful callback certified. Fe does not
prove that an arbitrary preflight is non-mutating or that an arbitrary
returning evaluator honored the deployment/model protocol. The capsule hash
provides unauthenticated self-consistency, not a signature, authorship, or
authority; anyone able to change the payload can recompute it. The trusted
expected manifest comes from the local wrapper, not from the capsule itself.
Both registries are caller-owned and resettable, so neither provides global
uniqueness. The AccountingLedger seed is curated and `[1,17]` is only a local
minimum under the current shrink order. No cross-toolchain address stability,
fresh outer EVM per candidate, or production-ledger security claim is made.

See [PROVENANCE.md](PROVENANCE.md) for the contest boundary, prior-work
disclosure, starter reuse, and AI-assistance statement.

## License

Apache License 2.0.
