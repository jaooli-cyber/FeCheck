#!/usr/bin/env python3
"""Verify the reproducible AccountingLedger adapter manifest."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from Crypto.Hash import keccak


SOURCE_DOMAIN = b"FECHECK/ACCOUNTING-LEDGER/SOURCE-MANIFEST/V1"
SOURCE_FILES = (
    "tests/accounting-ledger/src/action.fe",
    "tests/accounting-ledger/src/contracts.fe",
    "tests/accounting-ledger/src/harness.fe",
    "tests/accounting-ledger/src/model.fe",
)
MANIFEST_PATH = "tests/accounting-ledger/src/manifest.fe"

EXPECTED_FE_VERSION = "26.5.0"
EXPECTED_FE_COMMIT = "3dab95f"
EXPECTED_FE_BINARY_SHA256 = (
    "3732fbe8a6e9d2ea3925d02d0e3a1478bc1e01d742c2be75d3ea7300c46c45f0"
)
EXPECTED_BACKEND = "sonatina"
EXPECTED_PROFILE = "test"
EXPECTED_OPTIMIZATION = 1

SEMANTIC_DOMAINS = {
    "LEDGER_ACTION_ENCODING_FINGERPRINT_V1": b"FECHECK/ACCOUNTING-LEDGER/ACTION-ENCODING/V1",
    "LEDGER_MODEL_FINGERPRINT_V1": b"FECHECK/ACCOUNTING-LEDGER/MODEL/V1",
    "LEDGER_FIXTURE_POLICY_FINGERPRINT_V1": b"FECHECK/ACCOUNTING-LEDGER/FIXTURE-POLICY/V1",
    "LEDGER_FAILURE_SCHEMA_FINGERPRINT_V1": b"FECHECK/ACCOUNTING-LEDGER/FAILURE-SCHEMA/V1",
    "LEDGER_SNAPSHOT_SCHEMA_FINGERPRINT_V1": b"FECHECK/ACCOUNTING-LEDGER/SNAPSHOT-SCHEMA/V1",
    "LEDGER_ADAPTER_LOGIC_FINGERPRINT_V1": b"FECHECK/ACCOUNTING-LEDGER/ADAPTER-LOGIC/V1",
}

MANIFEST_CONSTANTS = (
    "LEDGER_SOURCE_BUNDLE_KECCAK_V1",
    "LEDGER_SOURCE_BUNDLE_SHA256_V1",
    "LEDGER_TOOLCHAIN_FINGERPRINT_V1",
) + tuple(SEMANTIC_DOMAINS)


class ManifestCheckError(ValueError):
    """Raised when manifest evidence is missing, malformed, or inconsistent."""


@dataclass(frozen=True)
class SourceEvidence:
    preimage: bytes
    keccak256: bytes
    sha256: bytes


@dataclass(frozen=True)
class ToolchainEvidence:
    version: str
    commit: str
    binary_sha256: str
    descriptor: str
    fingerprint: bytes


def u256(value: int) -> bytes:
    """Encode a canonical unsigned 256-bit integer."""
    if value < 0 or value >= 1 << 256:
        raise ManifestCheckError("value is not a u256")
    return value.to_bytes(32, "big")


def keccak256(payload: bytes) -> bytes:
    digest = keccak.new(digest_bits=256)
    digest.update(payload)
    return digest.digest()


def normalize_source(raw: bytes, relative_path: str) -> bytes:
    """Apply the V1 newline policy without altering other source bytes."""
    normalized = raw.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise ManifestCheckError(
            f"{relative_path}: contains a non-CRLF carriage return"
        )
    if not normalized.endswith(b"\n"):
        raise ManifestCheckError(f"{relative_path}: final LF is required")
    return normalized


def source_manifest_preimage(repo_root: Path) -> bytes:
    """Build the canonical V1 source-bundle preimage."""
    chunks = [u256(len(SOURCE_DOMAIN)), SOURCE_DOMAIN, u256(len(SOURCE_FILES))]
    for index, relative_path in enumerate(SOURCE_FILES, 1):
        path_bytes = relative_path.encode("ascii")
        source_path = repo_root / relative_path
        try:
            raw = source_path.read_bytes()
        except OSError as exc:
            raise ManifestCheckError(
                f"cannot read source file {relative_path}: {exc}"
            ) from exc
        content = normalize_source(raw, relative_path)
        chunks.extend(
            (
                u256(index),
                u256(len(path_bytes)),
                path_bytes,
                u256(len(content)),
                content,
            )
        )
    return b"".join(chunks)


def source_evidence(repo_root: Path) -> SourceEvidence:
    preimage = source_manifest_preimage(repo_root)
    return SourceEvidence(
        preimage=preimage,
        keccak256=keccak256(preimage),
        sha256=hashlib.sha256(preimage).digest(),
    )


def semantic_fingerprints() -> dict[str, bytes]:
    """Derive semantic pins from exact raw ASCII domains."""
    return {
        constant_name: keccak256(domain)
        for constant_name, domain in SEMANTIC_DOMAINS.items()
    }


def _parse_literal(literal: str, constant_name: str) -> int:
    compact = literal.replace("_", "")
    base = 16 if compact.lower().startswith("0x") else 10
    try:
        value = int(compact, base)
    except ValueError as exc:
        raise ManifestCheckError(
            f"{constant_name}: invalid u256 literal {literal!r}"
        ) from exc
    if value < 0 or value >= 1 << 256:
        raise ManifestCheckError(f"{constant_name}: literal is not a u256")
    return value


def parse_manifest_constants(manifest_path: Path) -> dict[str, int]:
    """Read required literal u256 definitions from the Fe manifest."""
    try:
        source = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestCheckError(f"cannot read {manifest_path}: {exc}") from exc
    except UnicodeError as exc:
        raise ManifestCheckError(f"{manifest_path}: not valid UTF-8") from exc

    constants: dict[str, int] = {}
    literal = r"(0[xX][0-9a-fA-F_]+|[0-9][0-9_]*)"
    for name in MANIFEST_CONSTANTS:
        pattern = re.compile(
            rf"^[ \t]*pub[ \t]+const[ \t]+{re.escape(name)}"
            rf"[ \t]*:[ \t]*u256[ \t]*=[ \t]*"
            rf"(?:\r?\n[ \t]+)?{literal}"
            rf"[ \t]*(?://[^\r\n]*)?$",
            re.MULTILINE,
        )
        matches = pattern.findall(source)
        if len(matches) != 1:
            raise ManifestCheckError(
                f"{manifest_path}: expected exactly one literal definition of {name}; "
                f"found {len(matches)}"
            )
        constants[name] = _parse_literal(matches[0], name)
    return constants


def parse_fe_version(output: str) -> tuple[str, str]:
    """Parse the complete, canonical `fe --version` output."""
    match = re.fullmatch(
        r"fe ([0-9]+\.[0-9]+\.[0-9]+) \(([0-9a-f]{7,40})\)",
        output.strip(),
    )
    if match is None:
        raise ManifestCheckError(f"unexpected `fe --version` output: {output!r}")
    return match.group(1), match.group(2)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise ManifestCheckError(f"cannot hash Fe binary {path}: {exc}") from exc
    return digest.hexdigest()


def toolchain_descriptor(
    version: str,
    commit: str,
    binary_sha256: str,
    backend: str,
    profile: str,
    optimization: int,
) -> str:
    """Construct the exact ASCII descriptor committed by manifest V1."""
    token = re.compile(r"[A-Za-z0-9_.+-]+")
    for label, value in (("backend", backend), ("profile", profile)):
        if token.fullmatch(value) is None:
            raise ManifestCheckError(f"{label} is not a canonical descriptor token")
    return (
        f"fe={version};commit={commit};binary-sha256={binary_sha256};"
        f"backend={backend};profile={profile};opt={optimization}"
    )


def toolchain_evidence(
    fe_binary: Path, backend: str, profile: str, optimization: int
) -> ToolchainEvidence:
    """Measure and validate the exact Fe executable and test profile."""
    try:
        binary = fe_binary.resolve(strict=True)
    except OSError as exc:
        raise ManifestCheckError(f"cannot resolve Fe binary {fe_binary}: {exc}") from exc

    binary_sha256 = sha256_file(binary)
    preexecution_mismatches = []
    if binary_sha256 != EXPECTED_FE_BINARY_SHA256:
        preexecution_mismatches.append(
            f"Fe binary SHA-256 {binary_sha256}, expected {EXPECTED_FE_BINARY_SHA256}"
        )
    if backend != EXPECTED_BACKEND:
        preexecution_mismatches.append(
            f"backend {backend!r}, expected {EXPECTED_BACKEND!r}"
        )
    if profile != EXPECTED_PROFILE:
        preexecution_mismatches.append(
            f"profile {profile!r}, expected {EXPECTED_PROFILE!r}"
        )
    if optimization != EXPECTED_OPTIMIZATION:
        preexecution_mismatches.append(
            f"optimization {optimization}, expected {EXPECTED_OPTIMIZATION}"
        )
    if preexecution_mismatches:
        raise ManifestCheckError(
            "refusing to execute unpinned Fe toolchain: "
            + "; ".join(preexecution_mismatches)
        )
    try:
        completed = subprocess.run(
            [str(binary), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ManifestCheckError(f"cannot execute Fe binary {binary}: {exc}") from exc
    if completed.returncode != 0:
        raise ManifestCheckError(
            f"`{binary} --version` exited {completed.returncode}: "
            f"{completed.stderr.strip()}"
        )
    if completed.stderr.strip():
        raise ManifestCheckError(
            f"`{binary} --version` wrote unexpected stderr: {completed.stderr.strip()!r}"
        )
    version, commit = parse_fe_version(completed.stdout)

    mismatches = []
    if version != EXPECTED_FE_VERSION:
        mismatches.append(f"Fe version {version}, expected {EXPECTED_FE_VERSION}")
    if commit != EXPECTED_FE_COMMIT:
        mismatches.append(f"Fe commit {commit}, expected {EXPECTED_FE_COMMIT}")
    if mismatches:
        raise ManifestCheckError("Fe version mismatch: " + "; ".join(mismatches))

    descriptor = toolchain_descriptor(
        version, commit, binary_sha256, backend, profile, optimization
    )
    descriptor_bytes = descriptor.encode("ascii")
    return ToolchainEvidence(
        version=version,
        commit=commit,
        binary_sha256=binary_sha256,
        descriptor=descriptor,
        fingerprint=keccak256(descriptor_bytes),
    )


def manifest_mismatches(
    constants: dict[str, int], measured: dict[str, int]
) -> list[str]:
    """Describe every expected manifest value that differs from measurement."""
    return [
        f"{name}: manifest 0x{constants[name]:064x}, measured 0x{value:064x}"
        for name, value in measured.items()
        if constants[name] != value
    ]


def check_manifest(
    repo_root: Path,
    fe_binary: Path,
    backend: str,
    profile: str,
    optimization: int,
) -> tuple[SourceEvidence, ToolchainEvidence]:
    repo_root = repo_root.resolve()
    constants = parse_manifest_constants(repo_root / MANIFEST_PATH)
    sources = source_evidence(repo_root)
    toolchain = toolchain_evidence(fe_binary, backend, profile, optimization)

    measured = {
        "LEDGER_SOURCE_BUNDLE_KECCAK_V1": int.from_bytes(sources.keccak256, "big"),
        "LEDGER_SOURCE_BUNDLE_SHA256_V1": int.from_bytes(sources.sha256, "big"),
        "LEDGER_TOOLCHAIN_FINGERPRINT_V1": int.from_bytes(
            toolchain.fingerprint, "big"
        ),
    }
    measured.update(
        (name, int.from_bytes(fingerprint, "big"))
        for name, fingerprint in semantic_fingerprints().items()
    )
    mismatches = manifest_mismatches(constants, measured)
    if mismatches:
        raise ManifestCheckError("manifest mismatch:\n  " + "\n  ".join(mismatches))
    return sources, toolchain


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify pinned evidence")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--fe", type=Path, required=True, help="Fe executable used by CI")
    parser.add_argument("--backend", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--opt", type=int, required=True, dest="optimization")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.check:
        print("error: --check is required", file=sys.stderr)
        return 2
    try:
        sources, toolchain = check_manifest(
            args.repo_root,
            args.fe,
            args.backend,
            args.profile,
            args.optimization,
        )
    except ManifestCheckError as exc:
        print(f"adapter manifest check failed: {exc}", file=sys.stderr)
        return 1

    print("AccountingLedger adapter manifest OK")
    print(f"source preimage bytes: {len(sources.preimage)}")
    print(f"source Keccak-256: 0x{sources.keccak256.hex()}")
    print(f"source SHA-256: 0x{sources.sha256.hex()}")
    print(f"toolchain descriptor: {toolchain.descriptor}")
    print(f"toolchain fingerprint: 0x{toolchain.fingerprint.hex()}")
    for name, fingerprint in semantic_fingerprints().items():
        domain = SEMANTIC_DOMAINS[name].decode("ascii")
        print(f"{name} ({domain}): 0x{fingerprint.hex()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
