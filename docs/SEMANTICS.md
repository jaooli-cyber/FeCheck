# FeCheck semantics - implemented slices

This document describes behavior enforced by the current code and tests. It is
not a roadmap and distinguishes certified pure behavior from the experimental
stateful callback boundary.

## Attempt identity

`attempt_index` starts at zero and counts generated run attempts evaluated
before shrinking, including discards and the falsifying input. Shrink candidates
have separate accounting and do not consume attempt indices. Direct
regeneration derives the same value from:

- master seed;
- attempt index;
- generation fingerprint.

The generation fingerprint binds the complete strategy descriptor, generation
algorithm, and edge policy. Algorithm V1 includes the fixed RNG rejection cap.
Shrink budgets are part of the run fingerprint but not the attempt seed.

Range edges are evaluated first:

1. `lo`;
2. `lo + 1`, if distinct and in range;
3. `hi`, if not already present.

Edge attempts do not create or advance an RNG. Random attempts use a fresh
Keccak RNG derived from their own attempt seed.

`BoolStrategy` implements the generic strategy contract with canonical
fingerprint and value digest, ordered `false`/`true` edge metadata, one-word RNG
generation, and a single strict shrink step toward its configured origin. The
certified runner in this slice remains specialized to `U256Range`.

## Outcomes and accounting

A property returns exactly one of `Pass`, `Discard`, `Fail(FailureKey)`,
or `InfrastructureError(ErrorCode)`.

Configuration errors are rejected before the first attempt. Property failures
and infrastructure errors are never conflated.

For `Passed` or `Exhausted` runs:

```text
attempts = valid_cases + discards
```

For falsified runs:

```text
attempts = valid_cases + discards + 1
property_evaluations = attempts + shrink_evaluations
```

With `max_discards = 0`, the first discard exhausts the run. With
`target_valid_cases = 0`, a valid configuration passes without generation or
property evaluation.

The normative stateful counters in `RunStats` are `fixture_evaluations`,
`contract_deployments`, and `actions_executed`. There is no duplicate state
evaluation counter. `max_state_evaluations` limits `fixture_evaluations`.
Pure runners and pure replay require all three counters to remain zero.

## Scalar shrinking

The origin is tried first. Remaining candidates repeatedly move from the
current value toward the origin by the ceiling of half the remaining distance.
Examples:

```text
origin 0, value 12 -> 0, 6, 9, 10, 11
origin 0, value 13 -> 0, 6, 9, 11, 12
origin 5, value 2  -> 5, 4, 3
```

Shrinking never consumes RNG. A candidate is accepted only when it:

- remains inside the strategy domain;
- strictly reduces rank relative to the current value;
- fails with the original `FailureKey`.

Passes, discards, and different failure keys are counted separately. After an
acceptance, candidate enumeration restarts from the new value. The final value
is not reevaluated.

A complete result requires a full final pass with no acceptance. If the budget
is exhausted while a candidate is pending, status is `PartialBudget`. A zero
budget with an empty cursor is `CompleteLocal`.

## Canonical V1 hashing

`H` is Keccak-256 and returns one 32-byte word. Canonical preimages are byte
strings, not padded arrays of words:

```text
U256(x)                = x as exactly 32 bytes, big-endian
BYTES(x)               = U256(byte_length(x)) || x
ENCODE(word)           = U256(word)
FIELD(tag, word)       = U256(tag) || U256(32) || U256(word)
PREIMAGE(domain, fs)   = BYTES(ASCII(domain))
                         || U256(field_count)
                         || FIELD(1, fs[0]) || ... || FIELD(n, fs[n-1])
```

Zero and non-applicable fields are encoded explicitly. Domains are exact ASCII
with no right padding. The implementation uses Fe `AsBytes` and `ByteWriter`
with the exact preimage lengths.

The `U256Range` strategy fingerprint has ten fields:

1. strategy kind (`U256Range V1 = 1`);
2. bounds descriptor, `H(U256(lo) || U256(hi))`;
3. origin;
4. capacity (`NONE = 0`);
5. maximum actions (`NONE = 0`);
6. action-strategy descriptor (`NONE = 0`);
7. ordered-edge descriptor,
   `H(U256(count) || U256(edge0) || U256(edge1) || U256(edge2))`, with unused
   edge words set to zero;
8. edge-enumeration policy (`V1 = 1`);
9. shrink-enumeration policy (`V1 = 1`);
10. value-encoding version (`V1 = 1`).

The generation fingerprint has three fields: algorithm version, edge-policy
version, and strategy fingerprint. Algorithm V1 includes the fixed limit of 64
uniform-sampling rejections; changing that limit requires a new algorithm
version.

The run fingerprint has exactly eleven fields:

1. generation fingerprint;
2. suite ID;
3. run namespace;
4. target valid cases;
5. maximum discards;
6. maximum shrink evaluations;
7. maximum state evaluations;
8. maximum deployments;
9. digest-format version;
10. capsule-format version;
11. codec fingerprint.

The attempt seed has exactly three fields: master seed, zero-based attempt
index, and generation fingerprint. The scalar value digest has two fields:
strategy fingerprint and value. The U256 codec fingerprint is Keccak-256 of the
exact ASCII bytes `FECHECK/CODEC/U256/V1`.

For the scalar `u256` path, the five canonical domain preimage sizes are:

- `FECHECK/STRATEGY/V1`: 1,043 bytes;
- `FECHECK/GENERATION/V1`: 373 bytes;
- `FECHECK/RUN/V1`: 1,134 bytes;
- `FECHECK/ATTEMPT/V1`: 370 bytes;
- `FECHECK/VALUE/V1`: 272 bytes.

The fixture salt is
`Keccak256(PREIMAGE("FECHECK/FIXTURE/V1", fields))`, with seven word fields in
this exact order: run fingerprint, suite ID, run namespace, master seed,
attempt index, local evaluation index, and role tag. Its preimage is 754 bytes.
V1 role tags are Target = 1, ActorA = 2, and ActorB = 3.

`tools/oracle_vectors.py` independently constructs every byte, prints each
preimage, and verifies Keccak goldens with PyCryptodome 3.23.0. They cover
Bool strategy identities, the scalar seeded full-domain RNG branch, ActionSeq
logical encoding and dynamic value encoding, zero/one/full edge configurations,
the complete seed-plus-four-word random sequence chain, a sequence run
fingerprint, and the non-edge sequence attempt at index four through its
attempt seed, four RNG words, and dynamic value digest. The fixture vector
covers its exact 754-byte preimage. Fe tests also mutate every scalar strategy
and run field individually.

## Certified replay

`check_u256_certified` returns the ordinary structured outcome plus a capsule
only for a falsified run. Capsule V1 records:

- capsule, generation-algorithm, and edge-policy versions;
- suite ID and run namespace;
- master seed and falsifying attempt index;
- attempt identity, equal to the canonical attempt seed derived from master
  seed, attempt index, and generation fingerprint;
- generation and run fingerprints;
- failure key and reserved flags;
- original and reduced value digests;
- run statistics as prefix metadata;
- shrink statistics and shrink status.

`replay_u256_capsule` performs a deterministic preflight before property
evaluation: capsule/generation/edge-policy versions; local run configuration and
strategy; suite, namespace, flags, generation fingerprint, run fingerprint, and
attempt identity; then structural capsule statistics. Invalid local inputs are
reported as `ConfigurationError`; incompatible recorded evidence is reported as
`Incompatible`. It then regenerates only the recorded attempt and verifies its
original digest.

The replay does not execute prior attempts or reconstruct their verdicts. It
does validate that the recorded prefix metadata is structurally possible:
attempt index and count, valid/discard/failure accounting, configured budgets,
the shrink-category sum, the property-evaluation equation, and zero stateful
counters for this pure slice.

The fresh property evaluation is classified as follows:

- `Pass` -> `FailureNotObserved`;
- `Discard` -> `ReplayInputDiscarded`;
- infrastructure error -> `ReplayInfrastructureError`;
- another failure key -> `FailureKeyMismatch`;
- the same failure key -> repeat shrinking.

A same-key replay is `Reproduced` only when reduced digest, every shrink
counter, and shrink status match the capsule.

The pure sequence path uses the distinct `U256ActionSeqReplayCapsule` type, so a
scalar capsule cannot be supplied to sequence replay. The
`check_u256_action_seq_certified` and
`replay_u256_action_seq_capsule` entry points apply the same version,
configuration, identity, structural-statistics, and exact-shrink-evidence rules.
The sequence generation fingerprint additionally binds physical capacity,
maximum logical length, and the complete action strategy, while its run
fingerprint requires the ActionSeq codec. Replay regenerates only the recorded
attempt, validates the canonical dynamic sequence digest before evaluating the
property, and never executes the recorded prefix. This certificate covers the
pure sequence path only; it is not evidence of stateful EVM execution.

## Pure-property boundary

`check_u256_pure`, `check_u256_certified`, and `replay_u256_capsule` accept only
`P: PureU256Property`. Their sequence counterparts accept only
`P: PureU256ActionSeqProperty<N>`. Both `evaluate` methods have an empty Fe
effect row, so effectful counters or mutable-history dependencies cannot cross
the public certification boundary. Effect-forwarding adapters behind those
pure entry points exist only as `pub(ingot)` test and instrumentation
primitives. The prevalidated shrink
primitive is likewise ingot-internal; the checked runner and replay establish
its original-failure precondition.

Stateful EVM properties use a separate effect-forwarding adapter that creates a
fresh fixture and model for every evaluation. The public experimental runner
accepts such callbacks, but they are deliberately outside the pure
certification boundary.

## Stateful identity and admission foundation

The contract-free root foundation does not itself execute EVM properties. It
defines a fixed deployment plan, a complete logical evaluation context, the
canonical fixture salt above, and ingot-internal admission primitives that
check both state-evaluation and deployment capacity before committing any work.
A rejected admission returns the input statistics unchanged. An accepted
admission increments only `fixture_evaluations` and returns the required
deployment count. That count is not a persistent reservation. Before another
admission, the scheduler must complete and account for the admitted fixture;
inconsistent prior `fixture_evaluations` and `contract_deployments` are
rejected. Attempts, property evaluations, deployments, actions, and shrink
counters are the responsibility of the stateful scheduler and fixture
executor.

These low-level primitives require the scheduler to validate the global
RunConfig, codec, and caps first; they are not a public certified boundary.
Plan validation then requires a nonzero deployments-per-evaluation count and
checks
`max_state_evaluations <= max_deployments / deployments_per_evaluation`, using
division to avoid overflow. A zero state-evaluation budget is valid; attempting
an evaluation under it is rejected before any counter changes.

`StatefulRunRegistry` is a bounded, caller-owned duplicate detector for
`(suite_id, run_namespace)` pairs. Duplicate detection has precedence over a
full-registry error. The registry proves only the history carried by that
caller: constructing a new registry resets it, so it is not an EVM-global
namespace guarantee.

The foundation itself performs no CREATE2 deployment, proxy call, or model
execution. The separate experimental runner composes it with consumer-defined
callbacks. The manifest-bound layer described below verifies receipts and a
full-run replay but still delegates EVM effects to those callbacks.

## Experimental stateful ActionSeq runner

`check_u256_action_seq_stateful_experimental` specializes the current stateful
path to `ActionSeq<u256, N>` and fixes the fixture plan internally at three
deployments: Target, ActorA, and ActorB. The plan is not caller-selectable. The
root ingot owns deterministic generation, context construction, admission,
statistics, verdict classification, and shrinking; it imports no EVM capability
and contains no contracts.

Each evaluation follows this order:

1. propose state/deployment admission against the completed prior statistics;
2. call the adapter preflight with only the evaluation context;
3. after `Ready`, adopt `fixture_evaluations += 1`, then increment the original
   attempt or shrink evaluation and `property_evaluations`;
4. call the evaluator with the sequence and context;
5. if it returns, account for exactly three deployments and validate its action
   receipt before classifying the verdict.

An original evaluation uses `local_evaluation_index = 0`. Shrink candidates
keep the falsifying `attempt_index` and use dense local indices `1..Q` in actual
evaluation order. Candidate budget has precedence over domain/rank checks,
state admission, and preflight. A candidate is accepted only for the original
`FailureKey`; acceptance restarts enumeration from the new value without
resetting the local index. The final minimal value is not reevaluated.

For a conforming structured result:

```text
property_evaluations = fixture_evaluations = attempts + shrink_evaluations
contract_deployments = 3 * fixture_evaluations
```

`actions_executed` is the sum of callback receipts. Every receipt must satisfy
`actions_executed <= logical_length`; otherwise error 507 is returned after
counting the completed fixture but without accepting the impossible action
count. A `Pass` must additionally report every logical action executed;
reporting a strict prefix returns error 508. `Discard`, `Fail`, and
`InfrastructureError` may report a real prefix. A captured action call that was
attempted counts as executed; an uncaught call revert aborts the outer
evaluation and yields no structured statistics.

The caller-owned registry uses transactional adoption. Configuration, strategy,
or static-plan errors leave it unchanged. `target_valid_cases = 0` performs no
claim or callback. For a nonzero target, duplicate/full checks happen before
generation, but the proposed claim is returned only after the first preflight
reports `Ready`. A first admission or preflight error therefore leaves the
registry unchanged; every structured result after `Ready` carries the claim.
The registry remains bounded, resettable, and local to the caller.

The callback protocol is not proven by Fe's type system. In particular, Fe
forwards the consumer's EVM effect but cannot prove that preflight is
non-mutating or that a returning evaluator deployed the complete fixture and
created a fresh model. A direct typed CREATE2 collision, constructor revert, or
other uncaught deployment failure reverts the outer evaluation and returns no
`RunOutcome`. A zero-code preflight observation does not exclude nonce,
constructor, or resource failures.

The experimental result alone is not a stateful replay certificate, a
cross-build address guarantee, or a global uniqueness proof. See
`docs/STATEFUL_RUNNER.md` for the complete protocol and evidence boundary.

## Manifest-bound stateful full-run recheck

`StatefulAdapterIdentityV1` contains the identity version, root protocol and
fixed three-role fixture-plan fingerprints, concrete fixture policy, action/model/snapshot/
failure/adapter fingerprints, target initcode/runtime, actor-template
initcode/runtime, source bundle, and toolchain fingerprint. The actor identity
field is an initcode template hash (AccountingLedger uses `Address::zero()`);
concrete fixture evidence carries the two actor initcode hashes instantiated
with the real target. Its canonical adapter fingerprint hashes these fixed
words under the stateful-adapter domain. The expected identity is a trusted
local input; capsule contents never select their own authority.

AccountingLedger derives six semantic fingerprints as Keccak-256 of the exact
raw ASCII domains for action encoding, model, fixture policy, failure schema,
snapshot schema, and adapter logic. `adapter_manifest.py` and the independent
oracle verify those bytes; no padding, trailing NUL, or normalized alias is
accepted.

For a strategy and `RunConfig`, the semantic identities are:

```text
ordinary_run = canonical pure run fingerprint
bound_run    = H(STATEFUL-RUN/V1,
                 ordinary_run,
                 adapter_fingerprint,
                 fixture_policy_fingerprint)
```

The original execution identity is
`H(EXEC-ORIGINAL/V1, bound_run, recorded_namespace)`. Generation continues to
use the ordinary strategy/generation identity and the original `RunConfig`.
The execution identity is carried separately as the fixture-salt domain.

Every `StatefulBoundEvaluationReceipt` binds the adapter, bound run, execution
fingerprint, suite, semantic and execution namespaces, master seed, attempt and
local evaluation indices, canonical candidate digest, fixture evidence,
verdict, failure/error fields, and actions executed. Concrete fixture evidence
may additionally bind per-evaluation addresses, initcode, and observed runtime
hashes. The ingot-level verifier recomputes this binding before exposing the
ordinary receipt to scheduler accounting. This detects mismatched or stale
receipts, not a callback that fabricates a self-consistent receipt.

A falsified bound run emits a `StatefulBoundReplayCapsuleV1`. Its payload words
are, in order:

```text
 0 domain/magic
 1 word count (36)
 2 format version
 3 generation algorithm version
 4 edge-policy version
 5 protocol fingerprint
 6 fixture-policy fingerprint
 7 sequence capacity
 8 suite ID
 9 recorded semantic namespace
10 master seed
11 falsifying attempt index
12 attempt identity
13 generation fingerprint
14 ordinary run fingerprint
15 bound run fingerprint
16 adapter fingerprint
17 failure kind
18 failure detail
19 flags
20 original digest
21 reduced digest
22..28 seven RunStats fields
29..33 five ShrinkStats fields
34 shrink-status tag
35 capsule digest
```

The digest is `Keccak256` of words `0..34`; it excludes word 35. The external
wire is exactly 36 big-endian words / 1,152 bytes. Decoding rejects non-exact
length, invalid magic, word count, versions, flags, status tags, out-of-range
capacity, or digest; recheck requires exact local capacity. These stateful
domain hashes are direct fixed-word Keccak preimages;
they are intentionally distinct from the tagged length-prefixed codec scheme
described for strategy/run fingerprints above. The digest supplies only
unauthenticated integrity/self-consistency: anyone able to alter the payload can
recompute it. It is not a signature, origin, or authorship proof.

Recheck first validates the trusted identity, capsule digest and fields,
strategy/config/generation/bound identities, attempt identity, regenerated
original digest, and overflow-safe structural statistics. This is completed
before callbacks. The replay namespace must differ from the recorded namespace;
its execution fingerprint is:

```text
H(EXEC-REPLAY/V1, bound_run, capsule_digest, replay_namespace)
```

The original `RunConfig` and semantic namespace are not rewritten. The new
execution identity affects fixture salts and the replay registry only. Recheck
then executes exactly attempts `0..capsule.attempt_index` on a non-divergent
prefix, including the historical falsifying attempt, followed by its complete
shrink path. A terminal earlier failure or infrastructure divergence stops at
that point for mismatch/error classification; no path executes a later attempt.
`Reproduced` requires the same failure key, original/reduced digests, all seven
run counters, all five shrink counters, and
shrink status.

`StatefulReplayRegistry` is independent from `StatefulRunRegistry`, bounded to
eight caller-owned entries, and keyed by `(suite_id, replay_namespace)`.
A proposed claim is adopted only after the first `Ready` preflight, so an early
validation/admission/preflight failure preserves the input registry. Resetting
or replacing either registry resets its knowledge; neither proves global EVM
uniqueness.

The generic layer remains verified rather than certified: Fe cannot prove the
effectful callback protocol. AccountingLedger supplies a specialized wrapper
that fixes the expected manifest, observes target and both proxy runtime hashes
before actions, and binds those hashes, three addresses, and both concrete
actor initcode hashes into fixture evidence.

## Test-only EVM capability evidence

The separate `tests/evm-probes` ingot depends on the root library but is not
part of its public API or build roots. It verifies, on Fe 26.5.0, that canonical
role salts can deploy one mutable target and two target-bound actor proxies. For every
fixture, all three addresses are predicted and checked for observed code
occupancy before the first deployment. The deployed addresses equal both
`predict_create2` and the explicit `create2_address(init_code_hash)` formula,
including the proxy constructor argument.

Two logical evaluations are deployed in one outer EVM with local indices zero
and one. Their six tested salts and addresses are distinct. Mutating either
target leaves the other target's storage unchanged, and each proxy remains
bound to its own target. Calls through ActorA and ActorB make the target observe
the corresponding proxy as `ctx.caller()`; recipient identity remains separate,
including a self-alias case.

This is observational capability evidence, not a universal CREATE2 availability
proof. A test-local preflight detects nonzero code at an occupied predicted
address and demonstrates that the other two roles were not deployed. A zero
`extcodesize` does not prove an account has zero nonce and does not guarantee a
constructor or CREATE2 will succeed.

A repeated direct typed CREATE2 reverts the outer evaluation. A constructor
revert is also observed at the outer boundary with an exact selector. A separate
factory microprobe shows that an enclosing `try_call` can capture both an empty
collision revert and a constructor payload. The factory is not part of the
three-contract fixture, its deployments are not included in stateful
accounting, and that capture path has not been adopted by a runner.

The root ingot emits no deployable contract artifacts; only the separate probe
ingot contains the five contracts used for this evidence.

These probes alone do not establish the experimental scheduler, its property
adapter, model, deployment/action statistics, or shrinking; that separate
integration evidence lives in `tests/stateful-runner`. Neither probe suite alone
establishes the manifest-bound capsule/recheck, fresh global EVM, or cross-build
address stability. That replay evidence lives in the root tests and the
specialized AccountingLedger ingot. Concrete addresses are fixture evidence,
not logical failure identity or capsule fields. See `docs/EVM_PROBES.md` and
`docs/STATEFUL_RUNNER.md` for the evidence boundaries.

## Action sequence boundary

`ActionSeq<A, N>` stores a fixed initialized array and a private logical
length. Public code can construct a checked value, read its logical length, and
request an item only inside the active prefix. It cannot inspect the physical
tail. The current canonical strategy is deliberately specialized to
`ActionSeq<u256, N>` with `N <= 4`; this bound is part of V1 behavior, not an
implicit compiler limit.

The canonical logical encoding is byte-exact:

```text
ENCODE(seq) = U256(len)
              || for i = 0..len-1: U256(32) || U256(item[i])
descriptor  = Keccak256(ENCODE(seq))
```

The per-item `U256(32)` is the encoded-item byte length. Only `len` and the
active prefix participate; physical capacity and initialized tail values do
not. The canonical value digest does not substitute the descriptor for the
value. Its second tagged field contains `ENCODE(seq)` itself:

```text
Keccak256(
  LP("FECHECK/VALUE/V1") || U256(2)
  || FIELD(1, U256(strategy_fingerprint))
  || FIELD(2, ENCODE(seq))
)
```

`action_seq_u256_digest_spike` remains available only to reproduce prior
non-wire feasibility evidence and is never used by the canonical path.

The ten sequence-strategy fingerprint fields are:

1. sequence strategy kind (`ActionSeq<u256> V1 = 3`);
2. no sequence-level bounds descriptor (`0`);
3. canonical empty-sequence descriptor;
4. physical capacity `N`;
5. maximum logical actions;
6. complete `U256Range` action-strategy fingerprint;
7. ordered descriptor of the unique sequence edges;
8. edge-enumeration policy (`V1 = 1`);
9. shrink-enumeration policy (`V1 = 1`);
10. value-encoding version (`V1 = 1`).

The unique edges are the empty sequence, one origin action when allowed, and
`max_actions` origin actions when distinct. Their descriptor is
`Keccak256(U256(count) || edge_0 || edge_1 || edge_2)`; unused descriptor
slots are zero. Edges do not consume RNG. A random attempt samples logical
length first, then invokes the action generator for every physical slot
`0..N-1`, including inactive slots. Attempt identity and the fresh Keccak RNG
follow the same master-seed/index/generation-fingerprint derivation as the
scalar runner. Changing that consumption order requires an algorithm-version
change.

Candidate order is exact:

1. delete every contiguous block with `block_len = len..1` and
   `start = 0..len-block_len`;
2. shrink active actions from left to right using scalar candidate order.

The incremental cursor carries both the validated strategy and its source; the
next-step API accepts only that cursor, so callers cannot resume enumeration
under a different strategy.

Deletion compacts the active prefix and fills its now-inactive storage with the
action origin. Duplicate block-deletion candidates are suppressed by exact
logical equality, never by hash. The structural order is
`(logical length, ordered action ranks)`, compared directly without lossy
packing into a `u256`. Exhaustive tests compare every emitted candidate with a
separate reference enumerator, assert in-domain strict rank reduction and
uniqueness for all sequences over `0..2` through length three, and exercise a
1,038-candidate Capacity-4 worst case to completion.

The kernel, exhaustive small-domain tests, and effect-free pure sequence runner
are implemented. The public runner accepts only
`PureU256ActionSeqProperty<N>`; an effect-forwarding callable exists only for
ingot-internal instrumentation. It preserves the original `FailureKey`,
restarts block deletion after every acceptance, distinguishes
`CompleteLocal` from `PartialBudget` at the candidate boundary, and maintains
the same attempt/shrink accounting equations as the scalar runner. A sequence
run requires `action_seq_u256_codec_fingerprint()`; scalar and sequence codecs
are rejected across runners before property evaluation. Pure sequence length
does not increment stateful counters or `actions_executed`.

The pure sequence runner now has certified capsules and direct replay. Its
distinct capsule binds all sequence strategy and run identity described above,
and replay checks the original canonical digest before property evaluation,
then reproduces the exact failure-key-preserving shrink evidence. Stateful
evaluation additionally creates a fresh fixture and model for every evaluated
original or candidate through the callback boundary. The manifest-bound
stateful layer emits a canonical capsule and verifies an exact full-run recheck
under fresh execution identity. Type-level proof of arbitrary adapter effects
is not claimed.
