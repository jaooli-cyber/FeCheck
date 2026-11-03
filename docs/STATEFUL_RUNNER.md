# Experimental stateful ActionSeq runner

Evidence date: 2026-11-03. Toolchain: Fe 26.5.0 (`3dab95f`).

`check_u256_action_seq_stateful_experimental` is FeCheck's first executable
stateful scheduler. It is deliberately named experimental: the root ingot owns
deterministic scheduling and accounting, while consumer callbacks own EVM
observation and execution under a protocol the Fe type system does not prove.
It is not a certified runner.

`check_u256_action_seq_stateful_bound_v1` and
`recheck_u256_action_seq_stateful_bound_v1` add a manifest-bound capsule and a
verified full-run recheck without changing that callback trust boundary.

## Fixed three-role boundary

The runner is specialized to `ActionSeq<u256, N>` and fixes the fixture plan at
three successful deployments per evaluated input:

1. Target;
2. ActorA, bound to Target;
3. ActorB, bound to Target.

The caller cannot substitute another deployment count. The root ingot contains
no contracts and imports no `Evm`; the concrete fixture lives in the separate
`tests/stateful-runner` ingot. Effects from its preflight and evaluator are
forwarded through the two callable effect rows.

The preflight receives only `StatefulFixtureRequest { context }`. It must
predict and observe all three destinations before any typed deployment and must
not mutate the EVM. `Ready` means only that the adapter elects to proceed; a
zero-code observation is not a universal CREATE2 availability proof.

The evaluator receives `StatefulActionSeqRequest { value, context }`. Returning
a `StatefulEvaluationReceipt` is the adapter's assertion that it deployed the
complete fresh fixture, created a fresh local model, and reports the exact
number of actions attempted. The root can validate the receipt's logical bounds
but cannot prove those EVM facts.

## Evaluation identity and order

The context separates semantic run identity from execution identity. Generation,
the `RunConfig`, candidate digests, and capsule validation remain tied to the
semantic namespace. Fixture salts additionally use `fixture_domain` and
`execution_namespace`.

The legacy experimental runner sets its semantic and execution identities to
the same values, preserving its original vectors. A bound original run uses:

```text
bound_run          = H(STATEFUL-RUN/V1, ordinary_run, adapter, fixture_policy)
original_execution = H(EXEC-ORIGINAL/V1, bound_run, recorded_namespace)
```

Original attempts use local index zero. Shrink evaluations retain the
falsifying attempt index and consume dense local indices beginning at one.
Invalid candidates and candidates rejected before a `Ready` preflight do not
consume an evaluation index.

For every original or shrink candidate that reaches the adapter, the order is:

```text
candidate generation/validation
-> state/deployment admission proposal
-> observational preflight
-> commit fixture and attempt-or-shrink counters
-> evaluator
-> account three deployments and the action receipt
-> classify verdict
```

Shrink budget is checked while a candidate is pending, before candidate-domain
validation, state admission, or preflight. It therefore wins if shrink and
state budgets are exhausted together. Same-key failures are accepted and
restart enumeration from the smaller value; passes, discards, and different
failure keys are rejected in separate counters. No final reevaluation occurs.

## Counters and receipts

For every conforming structured outcome:

```text
PE = fixture_evaluations = attempts + shrink_evaluations
contract_deployments = 3 * fixture_evaluations
```

Here `PE` is `property_evaluations`. A preflight or admission error consumes
none of these counters. An evaluator that returns consumes the evaluation and
three deployment slots even when its verdict is `InfrastructureError`.

`actions_executed` is receipt-driven:

- a count greater than the sequence length returns protocol error 507; the
  fixture/deployment counters remain, but the impossible action count is not
  added;
- `Pass` requires the count to equal the sequence length; a strict prefix is
  added as a physically possible observation and then returns protocol error
  508;
- `Discard`, `Fail`, and `InfrastructureError` may return a real prefix;
- an action whose revert is captured by the adapter counts when it was
  attempted; an uncaught revert yields no structured result.

## Registry transaction

`StatefulRunRegistry` is caller-owned, fixed-capacity, and resettable. For a
nonzero target, duplicate/full checks occur before generation, but a new claim
is only adopted after the first `Ready` preflight. Consequently:

- configuration, strategy, or static-plan errors preserve the input registry;
- `target_valid_cases = 0` passes without claiming or invoking callbacks;
- a generation, admission, or preflight error before the first `Ready`
  preserves it;
- any structured path after the first `Ready` returns the adopted claim.

This transaction avoids consuming one of eight entries when no fixture starts.
It does not make the registry global or persistent. Replacing it discards its
history.

## Manifest-bound receipts and capsule

`StatefulAdapterIdentityV1` commits to the root protocol and fixed fixture plan,
the adapter's concrete fixture policy, action encoding, model, snapshot and
failure schemas, adapter logic, target initcode/runtime, actor-template
initcode/runtime, source bundle, and toolchain/build profile. The actor initcode
field is explicitly the template hash for `Address::zero()`; concrete fixture
evidence carries the two real actor initcode hashes instantiated with that
fixture's target. The expected identity is a trusted local input. The capsule
cannot appoint its own authority.

A bound evaluator returns a `StatefulBoundEvaluationReceipt`. Its binding
fingerprint commits to:

- adapter and bound-run fingerprints;
- semantic and execution namespaces and the execution fingerprint carried as
  `fixture_domain`;
- suite, master seed, attempt index, and local evaluation index;
- canonical candidate digest;
- fixture-evidence fingerprint;
- verdict, failure/error detail where applicable, and actions executed.

The generic verifier checks that binding before ordinary scheduler accounting.
The AccountingLedger specialization constructs fixture evidence from the three
deployed addresses, both actual actor initcode hashes, and their three observed
`extcodehash` values. It compares the runtime hashes before any binding, state,
or action check. An arbitrary callback can still lie consistently, which is why
the generic API says bound and verified rather than certified.

A falsified bound run emits `StatefulBoundReplayCapsuleV1`. The canonical V1
wire is exactly 36 big-endian words (1,152 bytes):

```text
0      stateful capsule domain/magic
1      word_count = 36
2..34  versions, policies, run/adapter identity, failure and all counters
35     Keccak-256 of words 0..34
```

The 35-word payload includes capacity, suite, recorded semantic namespace,
seed, attempt identity, generation/ordinary/bound fingerprints, original and
reduced digests, all seven `RunStats`, all five `ShrinkStats`, and shrink-status
tag. The digest excludes its own word. The raw decoder requires exactly 1,152
bytes and rejects truncation, trailing bytes, unknown versions/flags/tags,
capacity mismatch at recheck, and digest mismatch. The hash provides only
unauthenticated self-consistency: anyone who can change the payload can
recompute it. It is not a signature and does not authenticate an author.

## Full-run recheck

A recheck receives the original `RunConfig` unchanged plus a replay namespace
different from the recorded namespace. It derives:

```text
replay_execution = H(EXEC-REPLAY/V1,
                     bound_run,
                     capsule_digest,
                     replay_namespace)
```

Only execution identity and fixture salts change. Candidate generation,
semantic run identity, digests, and the expected deterministic run remain
unchanged. Static validation rejects impossible counters and budget/status
combinations before callbacks.

On a non-divergent prefix, the recheck executes exactly attempts
`0..capsule.attempt_index`, including the historical falsifying attempt, then
repeats its shrink path. A terminal earlier failure or infrastructure divergence
stops immediately for mismatch/error classification; no path executes a later
attempt. `Reproduced` requires equality of the failure key, original and reduced
digests, all seven run counters, all five shrink counters, and shrink
status.
A pass/exhaustion is `FailureNotObserved`; callback failures remain structured
replay infrastructure errors; any exact-evidence difference is identified as
`EvidenceMismatch`.

`StatefulReplayRegistry` is separate from `StatefulRunRegistry` and keys
`(suite_id, replay_namespace)`. Its claim is transactional: rejection
before the first `Ready` preflight preserves the input registry; work after
`Ready` adopts the claim. Like the run registry, it has eight entries, is
caller-owned and resettable, and proves no global uniqueness.

## Executable evidence

The root suite exercises configuration/plan/registry precedence; zero target;
pass, discard, exhaustion, fail, and infrastructure outcomes; exact contexts;
state and shrink-budget precedence; original and shrink preflight failures;
evaluator infrastructure; both receipt-protocol errors; mixed shrink verdicts;
and exact registry adoption. The root contains 108 tests and remains
contract-free. The bound-recheck suite covers identity/receipt mismatch, wire
roundtrip and raw-length rejection, digest self-consistency, replay-registry
transactions, exact evidence comparison, fresh execution identity, and
overflow-safe pre-callback validation.

The isolated `tests/stateful-runner` golden uses the public runner and two
consumer-defined callables sharing one mutable EVM provider. In one test it
observes and deploys a fresh Target/ActorA/ActorB fixture for every original
and candidate evaluation, checks every target starts at zero, checks both
proxies remain bound, alternates actions through A and B, and compares target
state against a new local model. Its exact result is:

```text
attempts = 3
valid_cases = 2
shrink_evaluations = 5
accepted = 1
rejected_pass = 4
property_evaluations = fixture_evaluations = 8
contract_deployments = 24
actions_executed = 8
minimal sequence length = 2
```

All eight preflights observe three no-code destinations before their evaluator
runs. Thus the tested execution completes with twenty-four non-reused deployed
destinations in one EVM. A second `should_revert` test reuses one identity and
confirms that direct typed CREATE2 collision still aborts outside the structured
runner result.

Reproduce with:

```sh
fe fmt --check
fe fmt --check tests/stateful-runner
fe check . --profile dev
fe check tests/stateful-runner --profile dev
fe test . --backend sonatina --profile test -O 1 --jobs 1
fe test tests/stateful-runner --backend sonatina --profile test -O 1 --jobs 1
```

## Non-certification boundary

The verified recheck does not prove any of the following:

- that an arbitrary preflight is non-mutating;
- that an arbitrary returning evaluator deployed all three contracts or used a
  fresh model;
- that zero observed code implies CREATE2 success;
- that the caller-owned registry prevents reuse after it is reset;
- that addresses remain stable across compiler/build changes;
- that a new outer EVM is created for each evaluation;
- that this scheduler golden by itself establishes AccountingLedger behavior.

The bound identity does commit to bytecode, source, model/schema identities,
fixture policy, and toolchain; it deliberately does not promise cross-build
address stability. The capsule supports deterministic full-run replay, but its
digest is unauthenticated and recomputable, not a signature; the generic
callback remains a trust boundary.

The separate [`ACCOUNTING_LEDGER.md`](ACCOUNTING_LEDGER.md) demonstration fixes
a concrete trusted identity, observes runtime hashes before actions, and
supplies end-to-end EVM replay evidence under those limits.

The golden establishes behavior for its concrete adapter on the pinned
toolchain. Statefulness is isolated by fresh contracts and a fresh local model
inside one outer EVM, not by snapshots, reverts, or replacement of the EVM
provider.
