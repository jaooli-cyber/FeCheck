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


def encode_action_seq(values: list[int]) -> bytes:
    return u256(len(values)) + b"".join(
        u256(32) + u256(value) for value in values
    )


seq79_preimage = encode_action_seq([7, 9])
seq79_hash = keccak256(seq79_preimage)
seq_empty_hash = keccak256(encode_action_seq([]))
seq_one_hash = keccak256(encode_action_seq([0]))
seq_four_hash = keccak256(encode_action_seq([0, 0, 0, 0]))

action_seq_codec_preimage = b"FECHECK/CODEC/ACTIONSEQ-U256/V1"
action_seq_codec_hash = keccak256(action_seq_codec_preimage)
action_bounds_hash = keccak256(u256(0) + u256(1000))
action_edges_hash = keccak256(u256(3) + u256(0) + u256(1) + u256(1000))
_, action_strategy_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [1, as_int(action_bounds_hash), 0, 0, 0, 0, as_int(action_edges_hash), 1, 1, 1],
)
action_seq_edges_hash = keccak256(
    u256(3) + seq_empty_hash + seq_one_hash + seq_four_hash
)
action_seq_strategy_preimage, action_seq_strategy_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [
        3,
        0,
        as_int(seq_empty_hash),
        4,
        4,
        as_int(action_strategy_hash),
        as_int(action_seq_edges_hash),
        1,
        1,
        1,
    ],
)
action_seq_value_preimage = (
    encode_bytes(b"FECHECK/VALUE/V1")
    + u256(2)
    + field(1, action_seq_strategy_hash)
    + field(2, seq79_preimage)
)
action_seq_value_hash = keccak256(action_seq_value_preimage)

action_seq_max0_edges_hash = keccak256(
    u256(1) + seq_empty_hash + u256(0) + u256(0)
)
action_seq_max0_preimage, action_seq_max0_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [
        3,
        0,
        as_int(seq_empty_hash),
        4,
        0,
        as_int(action_strategy_hash),
        as_int(action_seq_max0_edges_hash),
        1,
        1,
        1,
    ],
)
action_seq_max1_edges_hash = keccak256(
    u256(2) + seq_empty_hash + seq_one_hash + u256(0)
)
action_seq_max1_preimage, action_seq_max1_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [
        3,
        0,
        as_int(seq_empty_hash),
        4,
        1,
        as_int(action_strategy_hash),
        as_int(action_seq_max1_edges_hash),
        1,
        1,
        1,
    ],
)

seq_three_hash = keccak256(encode_action_seq([0, 0, 0]))
action_seq_random_edges_hash = keccak256(
    u256(3) + seq_empty_hash + seq_one_hash + seq_three_hash
)
action_seq_random_strategy_preimage, action_seq_random_strategy_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [
        3,
        0,
        as_int(seq_empty_hash),
        3,
        3,
        as_int(full_strategy_hash),
        as_int(action_seq_random_edges_hash),
        1,
        1,
        1,
    ],
)
action_seq_random_generation_preimage, action_seq_random_generation_hash = hash_word_fields(
    "FECHECK/GENERATION/V1", [1, 1, as_int(action_seq_random_strategy_hash)]
)
action_seq_random_attempt_preimage, action_seq_random_attempt_hash = hash_word_fields(
    "FECHECK/ATTEMPT/V1",
    [7, 3, as_int(action_seq_random_generation_hash)],
)
action_seq_random_word0_preimage = action_seq_random_attempt_hash
action_seq_random_word0_hash = keccak256(action_seq_random_word0_preimage)
action_seq_random_word1_preimage = action_seq_random_word0_hash
action_seq_random_word1_hash = keccak256(action_seq_random_word1_preimage)
action_seq_random_word2_preimage = action_seq_random_word1_hash
action_seq_random_word2_hash = keccak256(action_seq_random_word2_preimage)
action_seq_random_word3_preimage = action_seq_random_word2_hash
action_seq_random_word3_hash = keccak256(action_seq_random_word3_preimage)
action_seq_random_value_preimage = (
    encode_bytes(b"FECHECK/VALUE/V1")
    + u256(2)
    + field(1, action_seq_random_strategy_hash)
    + field(2, encode_action_seq([]))
)
action_seq_random_value_hash = keccak256(action_seq_random_value_preimage)

VECTORS = {
    "action_seq_strategy_max0": (
        action_seq_max0_preimage,
        action_seq_max0_hash,
        "8f6185b61ef1943b0094d97cb12664d2e1f74b2854aa7c58f1fa77c6a190a954",
    ),
    "action_seq_strategy_max1": (
        action_seq_max1_preimage,
        action_seq_max1_hash,
        "dbe5a7ece6c34a7289b4f5ffec51d3015bd7e484d2576256583147fd98d6c73d",
    ),
    "action_seq_random_strategy": (
        action_seq_random_strategy_preimage,
        action_seq_random_strategy_hash,
        "3cf8baee16684205e58c1796c3589d041a0728b86e83d8b87a4f701e65d345a1",
    ),
    "action_seq_random_generation": (
        action_seq_random_generation_preimage,
        action_seq_random_generation_hash,
        "94a41a04931f9cbafadd0f70e7ed096043e0c2b4976268b6023eb42d3558ddda",
    ),
    "action_seq_random_attempt": (
        action_seq_random_attempt_preimage,
        action_seq_random_attempt_hash,
        "3b8883eb51de063cfa06defe2a6a096cceb48434d3cfacd9bd3886da40afaa41",
    ),
    "action_seq_random_word0": (
        action_seq_random_word0_preimage,
        action_seq_random_word0_hash,
        "dd0df08d35a78314cc3897cadeaead6a625f69eea128ff2964912f20d76061d4",
    ),
    "action_seq_random_word1": (
        action_seq_random_word1_preimage,
        action_seq_random_word1_hash,
        "0fccf7da5bd58be4df2b780f5e556e322414f6e706057e12c9c6674f72853241",
    ),
    "action_seq_random_word2": (
        action_seq_random_word2_preimage,
        action_seq_random_word2_hash,
        "aa0af77cb197663ca41aac83b1f42c88cbafa93f2f39453819eb24fcdd095eb6",
    ),
    "action_seq_random_word3": (
        action_seq_random_word3_preimage,
        action_seq_random_word3_hash,
        "af509bc2e136adfcd688139978d9772e09b1e3cec44c209a2cba221005cb4633",
    ),
    "action_seq_random_value": (
        action_seq_random_value_preimage,
        action_seq_random_value_hash,
        "7a311e9c48901abebd3c7f5e337034c52dbbfd02be8266cb61a827dfe080ee4a",
    ),
    "action_seq_79_descriptor": (
        seq79_preimage,
        seq79_hash,
        "73d301623f09544653fd3005bd55d8f38eb5e1b14a063cf7720ae69cc0c38495",
    ),
    "action_seq_codec": (
        action_seq_codec_preimage,
        action_seq_codec_hash,
        "b54d75c8a3cb0e657321665b2b2fc4c54aa2520a59fe9492bd484f0909c1aa60",
    ),
    "action_seq_strategy": (
        action_seq_strategy_preimage,
        action_seq_strategy_hash,
        "976794971cc060d47f80daa839dcddea1a5153293f0407de060ee8f953079523",
    ),
    "action_seq_value": (
        action_seq_value_preimage,
        action_seq_value_hash,
        "fc47ad2f0602fb50f9a7a65069ba7f9e11a80f34dc6857f7ef431aefc0fa0956",
    ),
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
