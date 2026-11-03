# FeCheck

FeCheck is a deterministic property-testing and counterexample-shrinking toolkit
written in Fe. It is being built for the Fe Builders Challenge.

The project starts with a pure `u256` vertical slice: reproducible generation by
attempt index, explicit pass/discard/fail outcomes, replay, and deterministic
shrinking. Stateful EVM model testing will be added only after that core is
verified.

## Toolchain

- Fe `26.5.0` (`3dab95f`)
- Linux `x86_64`
- Apache License 2.0

## Local verification

```sh
fe --version
fe fmt --check
fe check . --profile dev
fe test . --backend sonatina --profile test -O 1 --jobs 1
```

The contest implementation and repository history began after
`2026-11-03T00:00:00Z`.
