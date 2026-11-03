# EVM capability probes

Evidence date: 2026-11-03. Toolchain: Fe 26.5.0 (`3dab95f`).

This document records executable contest evidence. The contracts and tests live
in the separate `tests/evm-probes` ingot, which depends on the root `fecheck`
library. They do not become root build artifacts; the experimental public
stateful API is defined in the contract-free root independently of these probes.

## Verified matrix

| Boundary | Executable evidence |
|---|---|
| Canonical roles | Target, ActorA, and ActorB salts are pairwise distinct for each tested evaluation. |
| Exact CREATE2 formula | `predict_create2`, `create2_address(init_code_hash)`, and the deployed address agree for the target and both proxy instances. |
| Constructor binding | ActorA and ActorB use the predicted target as the identical constructor argument and report that binding after deployment. |
| Batch observation | All three predicted destinations are checked for code before the first deployment; all three contain code afterwards. |
| Occupied last role | Preoccupying ActorB is detected before Target or ActorA is deployed; the result identifies the occupied role and address. |
| Logical callers | The target observes ActorA and ActorB, never the test harness, as caller through their bound proxies. |
| Identity separation | Caller and recipient are recorded separately; A-to-A preserves equality, while B-to-A and A-to-B preserve direction. |
| Fresh fixture | Local evaluation indices 0 and 1 produce six distinct tested salts and addresses in the same outer EVM. Each target starts at zero and retains only its own mutations. |
| No-code call | A proxy bound to a predicted target with no code fails through outer `try_call`; empty-success behavior is not accepted as a valid target call. |
| Direct collision | A positive deployment proves the path works; the second identical typed CREATE2 is separately required to revert. |
| Constructor revert | The positive constructor path has code and responds; the negative path bubbles selector `0xfec0badd`. |
| Outer capture | A separate factory call captures an empty collision revert and the exact 32-byte constructor revert word while preserving the already deployed child. |

The fixture under test is exactly three contracts: one target plus two instances
of one high-level actor proxy type. The factory and its child contracts are
capability probes and are outside that fixture.

## Claim boundary

These tests support only the following claims:

- Fe 26.5.0 can predict and perform these concrete typed CREATE2 deployments.
- The tested canonical inputs separate both roles and two local evaluations.
- The two concrete target instances do not contaminate one another.
- Target-bound proxies preserve the two logical caller identities.
- Direct typed CREATE2 failures bubble, while an additional outer-call layer can
  observe their payloads.

They do not prove that a predicted address is universally available. A
zero-code observation cannot rule out every CREATE2 failure mode, including an
account with a nonzero nonce, constructor failure, or resource exhaustion. The
factory probe does not authorize mapping failures into `InfrastructureError`,
does not provide atomic fixture accounting, and is not part of the current
runner architecture.

This probe suite alone does not establish the experimental scheduler, its
stateful property/model adapter, deployment counter integration, or shrinking;
that separate evidence lives in `tests/stateful-runner`. Those two suites alone
do not claim a stateful capsule, stateful replay, fresh global EVM, cross-build
address stability, AccountingLedger behavior, or production collision
recovery. The separate `tests/accounting-ledger` ingot supplies the concrete
ledger evidence without extending those certification claims. Addresses never
enter logical failure identity. See [`STATEFUL_RUNNER.md`](STATEFUL_RUNNER.md)
for the scheduler boundary and [`ACCOUNTING_LEDGER.md`](ACCOUNTING_LEDGER.md)
for the demo boundary.

## Reproduce

```sh
fe fmt --check tests/evm-probes
fe check tests/evm-probes --profile dev
fe test tests/evm-probes --backend sonatina --profile test -O 1 --jobs 1
```

The capability-probe ingot contains 9 tests, the root ingot contains 97, and
the separate stateful-runner ingot contains 2. The AccountingLedger ingot adds
14, for 122 Fe tests in total. Keep
`--jobs 1` for predictable resource use while compiling embedded contracts.
