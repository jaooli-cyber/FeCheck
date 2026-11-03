# AccountingLedger

AccountingLedger is FeCheck's concrete state-machine demonstration. It exercises
the stateful action-sequence scheduler against a deliberately incorrect ledger,
reduces the resulting accounting violation, runs the same generated workload
against a corrected implementation, and performs a manifest-bound full-run
recheck with fresh fixture identities.

The demo is intentionally small: two actor contracts, deposits, transfers,
three actions at most, and no external asset. Its purpose is to make the model,
the EVM effects, every shrink decision, and the replay evidence inspectable.

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
code presence, role separation, and a zero initial snapshot. Before checking
bindings, state, or actions, the bound adapter observes all three
`extcodehash` values and compares them with its trusted manifest. A mismatch is
an infrastructure result with zero actions executed. This protocol also applies
to candidates that later return `Discard`. Per-evaluation evidence also binds
the actual ActorA and ActorB initcode hashes constructed with that fixture's
target address.

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

The independent Python oracle fixes the following AccountingLedger vector:

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
counters, then derives 25 AccountingLedger vectors for the six semantic
domains, adapter, bound-run, execution, capsule, and wire identities. These are
in addition to the 32 core vectors. The Fe ingot supplies the end-to-end EVM
evidence; neither side is used as the implementation of the other.

## Reproducible adapter manifest

The specialized entry points do not accept a caller-selected variant, identity,
preflight, or evaluator:

```text
check_accounting_ledger_buggy_bound_v1
check_accounting_ledger_fixed_bound_v1
recheck_accounting_ledger_buggy_bound_v1
recheck_accounting_ledger_fixed_bound_v1
```

The trusted buggy and fixed identities commit to the action/model/snapshot/
failure/fixture-policy schemas, adapter logic, source bundle, exact toolchain
profile, target initcode/runtime, and actor template initcode/runtime. Buggy and
fixed identities differ in both target initcode and target runtime. The actor
template hash is `init_code_hash<LedgerActorProxy>((Address::zero(),))`; each
fixture separately binds both actual
`init_code_hash<LedgerActorProxy>((fixture.target,))` values.

The source bundle covers exactly the normalized LF bytes of these four sorted
paths:

```text
tests/accounting-ledger/src/action.fe
tests/accounting-ledger/src/contracts.fe
tests/accounting-ledger/src/harness.fe
tests/accounting-ledger/src/model.fe
```

`manifest.fe` is deliberately excluded to avoid self-reference; `fe.toml` is
also outside this source bundle. The canonical preimage contains the domain,
file count, and each one-based index, relative POSIX path, byte length, and
untrimmed content. `tools/adapter_manifest.py` recomputes its Keccak-256 and
SHA-256 pins, executes and hashes the actual Fe binary, and verifies Fe 26.5.0
(`3dab95f`). Its descriptor also verifies the CI-declared policy of Sonatina,
profile `test`, and O1; it does not inspect a compiled artifact to infer those
settings.

The same verifier derives six semantic IDs from the exact raw ASCII domains for
action encoding, model, fixture policy, failure schema, snapshot schema, and
adapter logic. Any character change, including a trailing NUL, changes the ID.

## Bound run and full replay

The buggy run records semantic namespace `1`. Its adapter fingerprint and
fixture policy produce a bound-run fingerprint; the original execution
fingerprint supplies its fixture-salt domain. The capsule contains the same
`[2,17,25]` original, `[1,17]` reduced witness, stable failure key, and exact
`22/66/21` evaluation/deployment/action accounting plus the `18/2/8/8/0`
shrink counters.

The canonical capsule round-trips through an exact 1,152-byte raw wire. Its
36th word is the Keccak-256 digest of the preceding 35 words, excluding itself.
This is unauthenticated self-consistency, not a signature: anyone able to change
the payload can recompute the digest.

Replay namespace `3` is distinct from the recorded namespace. It changes only
the replay execution fingerprint and fixture salts; the original `RunConfig`,
semantic namespace, generation, and candidate digests remain unchanged. The
test proves that original and replay Target/ActorA/ActorB addresses differ,
that replay destinations have no code before replay and code afterwards, and
that exactly attempts `0..3` execute, followed by the historical failure's
shrink path; no later attempt executes. The complete prefix, failure, statistics,
digests, and status match exactly. The fixed identity rejects the buggy capsule
before callbacks. Repeating suite `LEDGER_SUITE_ID_V1` with the same replay
namespace and returned replay registry is also rejected before deployment; the
registry key is `(suite_id, replay_namespace)`.

## Honest claim boundary

This is a manifest-bound, verified full-run replay of this concrete audited
adapter. It is not a type-level certification of arbitrary stateful callbacks
and not a production-security proof.

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
- The specialized wrapper checks its concrete runtimes and binds the source and
  build, but the generic callback can still lie consistently about external
  effects.
- The capsule digest provides unauthenticated self-consistency, not signature,
  authorship, or authority. Trust comes from the expected local manifest.
- The run and replay registries are caller-owned and resettable; neither is a
  global EVM uniqueness registry.
- A new execution identity deliberately changes fixture addresses. No
  cross-build address-stability guarantee is made.
- The ledger has no asset, authorization policy, reentrancy surface, or
  production-security claim.

See [STATEFUL_RUNNER.md](STATEFUL_RUNNER.md) for the callback protocol and its
general limitations.

## Verification

```sh
fe fmt --check tests/accounting-ledger
fe check tests/accounting-ledger --profile dev
fe test tests/accounting-ledger --backend sonatina --profile test -O 1 --jobs 1
python tools/oracle_vectors.py
python -m unittest tools/test_adapter_manifest.py
python tools/adapter_manifest.py \
  --check \
  --fe "$(command -v fe)" \
  --backend sonatina \
  --profile test \
  --opt 1
```
