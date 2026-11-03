#!/usr/bin/env python3
"""Independent Keccak oracle for FeCheck V1 canonical fingerprints."""

from Crypto.Hash import keccak


def u256(value: int) -> bytes:
    if value < 0 or value >= 1 << 256:
        raise ValueError("value is not a u256")
    return value.to_bytes(32, "big")


def keccak256(payload: bytes) -> bytes:
    digest = keccak.new(digest_bits=256)
    digest.update(payload)
    return digest.digest()


def encode_bytes(payload: bytes) -> bytes:
    return u256(len(payload)) + payload


def field(tag: int, encoded: bytes) -> bytes:
    return u256(tag) + u256(len(encoded)) + encoded


def preimage(domain: str, values: list[int]) -> bytes:
    encoded_fields = b"".join(
        field(index, u256(value)) for index, value in enumerate(values, 1)
    )
    return encode_bytes(domain.encode("ascii")) + u256(len(values)) + encoded_fields


def hash_word_fields(domain: str, values: list[int]) -> tuple[bytes, bytes]:
    payload = preimage(domain, values)
    return payload, keccak256(payload)


def as_int(value: bytes) -> int:
    return int.from_bytes(value, "big")


LO = 0
HI = 100
ORIGIN = 0
BOUNDS_DESCRIPTOR = as_int(keccak256(u256(LO) + u256(HI)))
EDGES_DESCRIPTOR = as_int(keccak256(u256(3) + u256(0) + u256(1) + u256(100)))

strategy_preimage, strategy_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [1, BOUNDS_DESCRIPTOR, ORIGIN, 0, 0, 0, EDGES_DESCRIPTOR, 1, 1, 1],
)

generation_preimage, generation_hash = hash_word_fields(
    "FECHECK/GENERATION/V1", [1, 1, as_int(strategy_hash)]
)
attempt_preimage, attempt_hash = hash_word_fields(
    "FECHECK/ATTEMPT/V1", [7, 3, as_int(generation_hash)]
)
value_preimage, value_hash = hash_word_fields(
    "FECHECK/VALUE/V1", [as_int(strategy_hash), 12]
)
codec_preimage = b"FECHECK/CODEC/U256/V1"
codec_hash = keccak256(codec_preimage)
run_preimage, run_hash = hash_word_fields(
    "FECHECK/RUN/V1",
    [
        as_int(generation_hash),
        1,
        2,
        3,
        10,
        100,
        0,
        0,
        1,
        1,
        as_int(codec_hash),
    ],
)

BOOL_EDGES_DESCRIPTOR = as_int(
    keccak256(u256(2) + u256(0) + u256(1) + u256(0))
)
bool_false_preimage, bool_false_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [2, 0, 0, 0, 0, 0, BOOL_EDGES_DESCRIPTOR, 1, 1, 1],
)
bool_true_preimage, bool_true_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [2, 0, 1, 0, 0, 0, BOOL_EDGES_DESCRIPTOR, 1, 1, 1],
)

MAX_U256 = (1 << 256) - 1
full_bounds_descriptor = as_int(keccak256(u256(0) + u256(MAX_U256)))
full_edges_descriptor = as_int(
    keccak256(u256(3) + u256(0) + u256(1) + u256(MAX_U256))
)
_, full_strategy_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [1, full_bounds_descriptor, 0, 0, 0, 0, full_edges_descriptor, 1, 1, 1],
)
_, full_generation_hash = hash_word_fields(
    "FECHECK/GENERATION/V1", [1, 1, as_int(full_strategy_hash)]
)
full_attempt_preimage, full_attempt_hash = hash_word_fields(
    "FECHECK/ATTEMPT/V1", [7, 3, as_int(full_generation_hash)]
)
random_word_preimage = full_attempt_hash
random_word_hash = keccak256(random_word_preimage)

VECTORS = {
    "strategy": (
        strategy_preimage,
        strategy_hash,
        "a59f7fb423bdfb3a522cd2fd14e1cc8e6c0f85037ae66d6db21efa3243a8a5bd",
    ),
    "generation": (
        generation_preimage,
        generation_hash,
        "867b0175a87398842d331cbc2d5d05403f60d0430fa353c269ac88b9292e9006",
    ),
    "attempt": (
        attempt_preimage,
        attempt_hash,
        "14e91fbfb4ac893c0e9dd7bb77989bc6fd6544eccad4a5a60b5ca8344aa8e943",
    ),
    "value": (
        value_preimage,
        value_hash,
        "2440bb5729d555aa6c5e2ffb2badd479cb4b8e6e7e5f4b49f9118ea34cac5d0d",
    ),
    "codec": (
        codec_preimage,
        codec_hash,
        "3bcdf70d653ba1ab4cf526fc450367a00f561e4835125fcdc699acb697d4a679",
    ),
    "run": (
        run_preimage,
        run_hash,
        "5c79fe328f136f8b5f4bb2a4b0da81512473e0b5019ea4802ab6f6f241e48e11",
    ),
    "bool_false_strategy": (
        bool_false_preimage,
        bool_false_hash,
        "35204e01a91359abdfa1c9f57d3cd82411e879ba2130f60f97cef3965bd16df6",
    ),
    "bool_true_strategy": (
        bool_true_preimage,
        bool_true_hash,
        "3a0d0e05981ab502bee9deff3100349dca9c3a762c9a4b334f5cf0249b52ceb4",
    ),
    "full_domain_attempt": (
        full_attempt_preimage,
        full_attempt_hash,
        "9c40dca31d0754b82d7dede45fe229a980bf7bf951fa9bebbc79d687df4b8297",
    ),
    "random_full_domain_word": (
        random_word_preimage,
        random_word_hash,
        "c69c76789ef4fa0e760883627a670a1d2d4406218dcd5f0d72124c14a221d137",
    ),
}


def main() -> None:
    for name, (payload, digest, expected_hex) in VECTORS.items():
        actual_hex = digest.hex()
        if actual_hex != expected_hex:
            raise AssertionError(f"{name}: expected {expected_hex}, got {actual_hex}")
        print(f"{name}.preimage.len={len(payload)}")
        print(f"{name}.preimage.hex={payload.hex()}")
        print(f"{name}.keccak256=0x{actual_hex}")


if __name__ == "__main__":
    main()
