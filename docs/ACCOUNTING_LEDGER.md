# AccountingLedger

AccountingLedger is FeCheck's C6a state-machine demonstration. It exercises
the experimental stateful action-sequence scheduler against a deliberately
incorrect ledger, reduces the resulting accounting violation, and runs the
same generated workload against a corrected implementation.

The demo is intentionally small: two actor contracts, deposits, transfers,
three actions at most, and no external asset. Its purpose is to make the model,
the EVM effects, and every shrink decision inspectable.

## Boundary

The root FeCheck ingot remains contract-free. All deployable demo contracts and
their tests live in the separate `tests/accounting-ledger` ingot. Each property
evaluation uses this fixed fixture:

```text
Fe test harness
  |
  +-- Target: AccountingLedgerBuggy or AccountingLedgerFixed
  +-- ActorA proxy --CALL--> Target
  `-- ActorB proxy --CALL--> Target
```

Conceptual actor `A` is the address of ActorA and `B` is the address of ActorB.
A deposit is relayed by its actor. A transfer is relayed by its source actor and
names the recipient proxy as its destination.

Before every original or shrink evaluation, the adapter predicts all three
CREATE2 addresses and checks that they contain no code. The evaluator then
performs three typed deployments, verifies the predicted identities, bindings,
code presence, role separation, and a zero initial snapshot. This protocol also
applies to candidates that later return `Discard`.

## Packed action word

One `u256` contains the complete conceptual action:

```text
bits 0..1  amount: 0, 1, 2; 3 is reserved
bit 2      actor/from: 0=A, 1=B
bit 3      to: 0=A, 1=B
bit 4      kind: 0=Deposit, 1=Transfer
bits >=5   zero
```

The canonical encodings are:

| Action | Word |
| --- | ---: |
| `Deposit(A,n)` | `n` |
| `Deposit(B,n)` | `4+n` |
| `Transfer(A,A,n)` | `16+n` |
| `Transfer(B,A,n)` | `20+n` |
| `Transfer(A,B,n)` | `24+n` |
| `Transfer(B,B,n)` | `28+n` |

`Deposit` requires its unused `to` bit to be zero. Words
`3,7,8,9,10,11,12,13,14,15,19,23,27` are therefore reserved. Reserved words,
zero amounts, and transfers without enough model balance are property
`Discard` results. They are neither infrastructure errors nor logical failure
keys.

The current strategy is:

```text
U256Range { lo: 0, hi: 30, origin: 1 }
U256ActionSeqStrategy<3> { max_actions: 3 }
```

Origin `1` is `Deposit(A,1)`. This domain is designed for a clear shrink trace,
not for high acceptance rate: only 12 of its 31 words are positive canonical
actions before balance preconditions are considered.

## Pure model and execution order

The model contains `balance_a`, `balance_b`, and `total_shares`. A pure
`preview` operation either rejects the current action or returns a complete
predicted next model. It does not call the EVM and does not mutate its input.

- a deposit increases one balance and `total_shares`;
- a cross-actor transfer debits and credits without changing the total;
- a self-transfer is an explicit model no-op.

The evaluator processes one action at a time:

1. decode the word and check the model-only precondition;
2. compute the predicted next model without committing it;
3. issue exactly one call through the selected proxy;
4. classify a captured revert as a stable call failure;
5. read the post-call snapshot;
6. check accounting conservation before any field-by-field model comparison;
7. compare the snapshot with the predicted model;
8. commit the predicted model only when both checks pass.

An invalid word or failed precondition does not issue a call and does not
increase `actions_executed`. A call that is actually attempted does count,
including a call that returns a captured revert. `Pass` is possible only after
all logical actions have executed.

The main stable failure is
`INVARIANT/ACCOUNTING_CONSERVATION`. Its key contains no action index, amount,
balance, address, seed, or other reducible witness. Conservation has precedence
over the more general state/model mismatch, so every retained manifestation of
the aliasing bug has the same key.

## Bug and correction

The buggy transfer reads both balances before either write:

```text
source_before      = balance[caller]
destination_before = balance[to]
balance[caller]    = source_before - amount
balance[to]        = destination_before + amount
```

With a self-transfer, both map keys are the same. The second write overwrites
the debit with `balance + amount`, while `total_shares` remains unchanged.

The fixed target returns successfully without changing storage when
`caller == to`. Its ABI, storage meaning, proxy behavior, model, generator, and
property checks otherwise remain the same.

## Deterministic evidence

The independent Python oracle fixes the following C6a vector:

```text
master seed        1608
attempt index      3
random draws mod   [3,2,17,25]
original           [2,17,25]
minimal            [1,17]
```

The original decodes to:

```text
Deposit(A,2)
Transfer(A,A,1)
Transfer(A,B,1)
```

The accounting invariant fails after the second action, so the suffix transfer
is not executed. The current shrinker produces this complete trace (`P`, `D`,
and `F` mean Pass, Discard, and the matching conservation failure):

```text
[]          P
[25]        D
[2]         P
[17,25]     D
[2,25]      P
[2,17]      F  accept

[]          P
[17]        D
[2]         P
[1,17]      F  accept

[]          P
[17]        D
[1]         P
[1,1]       P
[1,9]       D
[1,13]      D
[1,15]      D
[1,16]      D
```

The reduced value is:

```text
Deposit(A,1)
Transfer(A,A,1)
```

Its expected buggy-run accounting is:

```text
attempts                    4
valid cases                 3
original discards           0
property/fixture evaluations 22
contract deployments        66
actions executed            21
shrink evaluations          18
accepted                    2
rejected Pass/Discard       8 / 8
rejected other failure key  0
status                      CompleteLocal
```

With the fixed target and a distinct namespace, the same strategy and seed pass
after four attempts, twelve deployments, and seven executed actions. Changing
the namespace changes the run and fixture identities but not action generation.

`tools/oracle_vectors.py` independently recomputes the scalar, sequence,
generation, attempt, and four RNG-word hashes. It also simulates the packed
decoder, pure model, buggy/fixed targets, current candidate order, trace, and
counters. The Fe ingot supplies the end-to-end EVM evidence; neither side is
used as the implementation of the other.

## Honest claim boundary

This is an experimental demonstration, not a certified stateful result.

- `[1,17]` is `CompleteLocal` under the current shrink order, not a global
  minimum.
- Seed `1608` is curated for a short deterministic demonstration. It is not
  evidence of unbiased discovery probability or broad protocol coverage.
- Every candidate receives newly deployed contracts, but all candidates in a
  test run still execute inside the same outer EVM. The demo does not create a
  new EVM process per candidate.
- `extcodesize == 0` is a conservative preflight observation, not a guarantee
  that a subsequent CREATE2 cannot revert.
- Direct typed CREATE2 failure still escapes the structured runner boundary.
- The scheduler accounts for three deployments when the callback returns; Fe's
  type system does not prove that the callback honored that obligation.
- Current run fingerprints do not bind target bytecode, proxy bytecode, the
  decoder, the model, or fixture policy.
- There is no stateful capsule, certified replay, external serialization, or
  cross-build address guarantee in this slice.
- The ledger has no asset, authorization policy, reentrancy surface, or
  production-security claim.

A future stateful replay boundary must authenticate the action encoding,
model/property version, failure schema, adapter and bytecode identities,
snapshot schema, fixture policy, and full run configuration. It must also use a
fresh replay identity in a fresh outer invocation.

See [STATEFUL_RUNNER.md](STATEFUL_RUNNER.md) for the callback protocol and its
general limitations.

## Verification

```sh
fe fmt --check tests/accounting-ledger
fe check tests/accounting-ledger --profile dev
fe test tests/accounting-ledger --backend sonatina --profile test -O 1 --jobs 1
python tools/oracle_vectors.py
```
