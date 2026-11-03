# Fe Builders Challenge submission - draft

This file is intentionally marked as a draft until the implementation, demo,
and public-release checks are complete.

- Project: FeCheck
- Repository: https://github.com/jaooli-cyber/FeCheck
- License: Apache-2.0
- Language/toolchain: Fe 26.5.0
- Status: active development
- Exact submission commit: to be fixed at release time

## Summary

FeCheck brings deterministic property testing, direct replay, and
failure-preserving shrinking to Fe. The verified pure slice already demonstrates
attempt-indexed generation, bounded unbiased randomness, structured outcomes,
canonical fingerprints, exact accounting, and budget-aware shrinking. Its
type-enforced pure boundary produces certified capsules that commit the failing
attempt identity, replay only that attempt, and verify recorded shrink evidence.

## Verification

```sh
fe fmt --check .
fe check . --profile dev
fe test . --backend sonatina --profile test -O 1 --jobs 1
python3 -m venv .venv-oracle
. .venv-oracle/bin/activate
python -m pip install -r tools/requirements-oracle.txt
python tools/oracle_vectors.py
```

See `README.md`, `docs/SEMANTICS.md`, and `PROVENANCE.md` for current scope,
semantics, and disclosure.
