# FeCheck semantics - implemented pure slice

This document describes behavior enforced by the current code and tests. It is
not a roadmap and does not claim unfinished stateful features.

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

The five canonical domains and exact V1 preimage sizes are:

- `FECHECK/STRATEGY/V1`: 1,043 bytes;
- `FECHECK/GENERATION/V1`: 373 bytes;
- `FECHECK/RUN/V1`: 1,134 bytes;
- `FECHECK/ATTEMPT/V1`: 370 bytes;
- `FECHECK/VALUE/V1`: 272 bytes.

`tools/oracle_vectors.py` independently constructs every byte, prints each
preimage, and verifies ten Keccak goldens with PyCryptodome 3.23.0, including
Bool strategy identities and the seeded full-domain RNG branch. Fe tests also
mutate every one of the ten strategy fields and eleven run fields individually.

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

## Pure-property boundary

`check_u256_pure`, `check_u256_certified`, and `replay_u256_capsule` accept only
`P: PureU256Property`. Its `evaluate` method has an empty Fe effect row, so
effectful counters or mutable-history dependencies cannot cross the public
certification boundary. Effect-forwarding callable adapters exist only as
`pub(ingot)` test and instrumentation primitives. The prevalidated shrink
primitive is likewise ingot-internal; the checked runner and replay establish
its original-failure precondition.

Stateful EVM properties require a separate adapter that creates a fresh fixture
and model for every evaluation. That adapter is not implemented in this slice.

## Action sequence boundary

`ActionSeq<A, N>` is currently a Copy-safe bounded representation. Its digest
function is named `action_seq_u256_digest_spike` and is intentionally non-wire:
it demonstrates that capacity and initialized tail bytes can be excluded from a
logical digest, but it is not the canonical V1 replay codec. Canonical sequence
generation, shrinking, and stateful evaluation remain pending.
