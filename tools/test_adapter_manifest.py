#!/usr/bin/env python3
"""Unit tests for the AccountingLedger adapter-manifest verifier."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

import adapter_manifest as manifest


class AdapterManifestTests(unittest.TestCase):
    def test_u256_is_fixed_width_and_rejects_out_of_range(self) -> None:
        self.assertEqual(manifest.u256(1), b"\x00" * 31 + b"\x01")
        self.assertEqual(manifest.u256((1 << 256) - 1), b"\xff" * 32)
        for value in (-1, 1 << 256):
            with self.subTest(value=value):
                with self.assertRaises(manifest.ManifestCheckError):
                    manifest.u256(value)

    def test_source_preimage_has_fixed_order_paths_and_normalized_lf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = [
                manifest.u256(len(manifest.SOURCE_DOMAIN)),
                manifest.SOURCE_DOMAIN,
                manifest.u256(len(manifest.SOURCE_FILES)),
            ]
            for index, relative_path in enumerate(manifest.SOURCE_FILES, 1):
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"file {index}\r\n".encode("ascii"))
                encoded_path = relative_path.encode("ascii")
                content = f"file {index}\n".encode("ascii")
                expected.extend(
                    (
                        manifest.u256(index),
                        manifest.u256(len(encoded_path)),
                        encoded_path,
                        manifest.u256(len(content)),
                        content,
                    )
                )
            expected_preimage = b"".join(expected)
            evidence = manifest.source_evidence(root)
            self.assertEqual(evidence.preimage, expected_preimage)
            self.assertEqual(evidence.keccak256, manifest.keccak256(expected_preimage))
            self.assertEqual(
                evidence.sha256, hashlib.sha256(expected_preimage).digest()
            )

    def test_source_policy_rejects_lone_cr_and_missing_final_lf(self) -> None:
        for payload, expected in (
            (b"bad\rline\n", "non-CRLF carriage return"),
            (b"missing LF", "final LF is required"),
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(manifest.ManifestCheckError, expected):
                    manifest.normalize_source(payload, "example.fe")

    def test_manifest_parser_reads_exact_u256_literals(self) -> None:
        contents = "\n".join(
            (
                "pub const LEDGER_SOURCE_BUNDLE_KECCAK_V1: u256 = 0x01",
                "pub const LEDGER_SOURCE_BUNDLE_SHA256_V1: u256 = 2_000",
                "pub const LEDGER_TOOLCHAIN_FINGERPRINT_V1: u256 =",
                "    0X0a // pin",
                *(
                    f"pub const {name}: u256 = {index}"
                    for index, name in enumerate(manifest.SEMANTIC_DOMAINS, 11)
                ),
                "",
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.fe"
            path.write_text(contents, encoding="utf-8")
            values = manifest.parse_manifest_constants(path)
        self.assertEqual(
            {name: values[name] for name in manifest.MANIFEST_CONSTANTS[:3]},
            {
                "LEDGER_SOURCE_BUNDLE_KECCAK_V1": 1,
                "LEDGER_SOURCE_BUNDLE_SHA256_V1": 2000,
                "LEDGER_TOOLCHAIN_FINGERPRINT_V1": 10,
            },
        )
        self.assertEqual(
            {name: values[name] for name in manifest.SEMANTIC_DOMAINS},
            {name: index for index, name in enumerate(manifest.SEMANTIC_DOMAINS, 11)},
        )

    def test_manifest_parser_rejects_expression_and_duplicate(self) -> None:
        valid_tail = "\n".join(
            (
                "pub const LEDGER_SOURCE_BUNDLE_SHA256_V1: u256 = 2",
                "pub const LEDGER_TOOLCHAIN_FINGERPRINT_V1: u256 = 3",
                *(
                    f"pub const {name}: u256 = {index}"
                    for index, name in enumerate(manifest.SEMANTIC_DOMAINS, 4)
                ),
                "",
            )
        )
        cases = (
            (
                "pub const LEDGER_SOURCE_BUNDLE_KECCAK_V1: u256 = OTHER\n"
                + valid_tail,
                "found 0",
            ),
            (
                "pub const LEDGER_SOURCE_BUNDLE_KECCAK_V1: u256 = 1\n"
                "pub const LEDGER_SOURCE_BUNDLE_KECCAK_V1: u256 = 4\n"
                + valid_tail,
                "found 2",
            ),
        )
        for contents, error in cases:
            with self.subTest(error=error):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "manifest.fe"
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaisesRegex(manifest.ManifestCheckError, error):
                        manifest.parse_manifest_constants(path)

    def test_version_parser_is_strict(self) -> None:
        self.assertEqual(
            manifest.parse_fe_version("fe 26.5.0 (3dab95f)\n"),
            ("26.5.0", "3dab95f"),
        )
        for output in (
            "26.5.0 (3dab95f)",
            "fe 26.5.0 3dab95f",
            "prefix fe 26.5.0 (3dab95f)",
        ):
            with self.subTest(output=output):
                with self.assertRaises(manifest.ManifestCheckError):
                    manifest.parse_fe_version(output)

    def test_toolchain_descriptor_matches_pinned_v1(self) -> None:
        descriptor = manifest.toolchain_descriptor(
            manifest.EXPECTED_FE_VERSION,
            manifest.EXPECTED_FE_COMMIT,
            manifest.EXPECTED_FE_BINARY_SHA256,
            manifest.EXPECTED_BACKEND,
            manifest.EXPECTED_PROFILE,
            manifest.EXPECTED_OPTIMIZATION,
        )
        self.assertEqual(
            descriptor,
            "fe=26.5.0;commit=3dab95f;binary-sha256="
            "3732fbe8a6e9d2ea3925d02d0e3a1478bc1e01d742c2be75d3ea7300c46c45f0;"
            "backend=sonatina;profile=test;opt=1",
        )
        self.assertEqual(len(descriptor), 139)
        self.assertEqual(
            manifest.keccak256(descriptor.encode("ascii")).hex(),
            "5aeb86a363465c7918ea97437c00f7f80f2863b4b8f7dad5edce728a3c8077a0",
        )

    def test_semantic_fingerprints_use_exact_raw_ascii_domains(self) -> None:
        expected = {
            "LEDGER_ACTION_ENCODING_FINGERPRINT_V1":
                "67d58f903806ee40c34cff6cb13414aecfb3683f94ddbaaf7496035d09070625",
            "LEDGER_MODEL_FINGERPRINT_V1":
                "c1423a868084918f2457dd0d09e75633e135e7b35a854e6bd8dbc65e0815d926",
            "LEDGER_FIXTURE_POLICY_FINGERPRINT_V1":
                "8428790e9e9db5de5013ff9db9c9d0f450be0d86247c34bf4854b380c858105a",
            "LEDGER_FAILURE_SCHEMA_FINGERPRINT_V1":
                "65242bbd8ded40b90e37ff842f83ccb18bc65bd14242bbd1146fbeeffc5983f0",
            "LEDGER_SNAPSHOT_SCHEMA_FINGERPRINT_V1":
                "6d5686d6260d162552aba0c3e17bd7585c780e6cbcdf30197f09fd3c3c562724",
            "LEDGER_ADAPTER_LOGIC_FINGERPRINT_V1":
                "6c95e6a147705c2a687d04bf122d69fa31d756405b7d8d9616fad2dee7e11e56",
        }
        fingerprints = manifest.semantic_fingerprints()
        self.assertEqual(
            {name: value.hex() for name, value in fingerprints.items()}, expected
        )
        for name, domain in manifest.SEMANTIC_DOMAINS.items():
            with self.subTest(name=name):
                self.assertEqual(fingerprints[name], manifest.keccak256(domain))
                self.assertNotEqual(
                    fingerprints[name], manifest.keccak256(domain + b"\x00")
                )

    def test_semantic_literal_mutation_is_reported(self) -> None:
        measured = {
            name: int.from_bytes(value, "big")
            for name, value in manifest.semantic_fingerprints().items()
        }
        constants = dict(measured)
        mutated = "LEDGER_MODEL_FINGERPRINT_V1"
        constants[mutated] ^= 1
        mismatches = manifest.manifest_mismatches(constants, measured)
        self.assertEqual(len(mismatches), 1)
        self.assertIn(mutated, mismatches[0])
        self.assertIn("manifest 0x", mismatches[0])
        self.assertIn("measured 0x", mismatches[0])

    def test_unpinned_binary_is_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "fe"
            binary.write_bytes(b"not the pinned Fe binary")
            with mock.patch.object(manifest.subprocess, "run") as run:
                with self.assertRaisesRegex(
                    manifest.ManifestCheckError,
                    "refusing to execute unpinned Fe toolchain",
                ):
                    manifest.toolchain_evidence(
                        binary,
                        manifest.EXPECTED_BACKEND,
                        manifest.EXPECTED_PROFILE,
                        manifest.EXPECTED_OPTIMIZATION,
                    )
                run.assert_not_called()

    def test_descriptor_rejects_field_injection(self) -> None:
        with self.assertRaisesRegex(
            manifest.ManifestCheckError, "canonical descriptor token"
        ):
            manifest.toolchain_descriptor(
                manifest.EXPECTED_FE_VERSION,
                manifest.EXPECTED_FE_COMMIT,
                manifest.EXPECTED_FE_BINARY_SHA256,
                "sonatina;profile=dev",
                manifest.EXPECTED_PROFILE,
                manifest.EXPECTED_OPTIMIZATION,
            )


if __name__ == "__main__":
    unittest.main()
