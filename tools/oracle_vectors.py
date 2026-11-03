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

action_seq_random_attempt4_preimage, action_seq_random_attempt4_hash = hash_word_fields(
    "FECHECK/ATTEMPT/V1",
    [7, 4, as_int(action_seq_random_generation_hash)],
)
action_seq_random4_word0_preimage = action_seq_random_attempt4_hash
action_seq_random4_word0_hash = keccak256(action_seq_random4_word0_preimage)
action_seq_random4_word1_preimage = action_seq_random4_word0_hash
action_seq_random4_word1_hash = keccak256(action_seq_random4_word1_preimage)
action_seq_random4_word2_preimage = action_seq_random4_word1_hash
action_seq_random4_word2_hash = keccak256(action_seq_random4_word2_preimage)
action_seq_random4_word3_preimage = action_seq_random4_word2_hash
action_seq_random4_word3_hash = keccak256(action_seq_random4_word3_preimage)
action_seq_random4_logical = encode_action_seq(
    [
        as_int(action_seq_random4_word1_hash),
        as_int(action_seq_random4_word2_hash),
        as_int(action_seq_random4_word3_hash),
    ]
)
action_seq_random4_value_preimage = (
    encode_bytes(b"FECHECK/VALUE/V1")
    + u256(2)
    + field(1, action_seq_random_strategy_hash)
    + field(2, action_seq_random4_logical)
)
action_seq_random4_value_hash = keccak256(action_seq_random4_value_preimage)

action_seq_run_preimage, action_seq_run_hash = hash_word_fields(
    "FECHECK/RUN/V1",
    [
        as_int(action_seq_random_generation_hash),
        31,
        41,
        3,
        10,
        100,
        0,
        0,
        1,
        1,
        as_int(action_seq_codec_hash),
    ],
)

fixture_preimage, fixture_hash = hash_word_fields(
    "FECHECK/FIXTURE/V1",
    [
        as_int(action_seq_run_hash),
        31,
        41,
        7,
        4,
        0,
        1,
    ],
)

# AccountingLedger C6a uses a compact one-word action domain.  These values are
# intentionally computed without importing FeCheck so the Python oracle remains
# an independent implementation of the canonical encoding and RNG chain.
LEDGER_LO = 0
LEDGER_HI = 30
LEDGER_ORIGIN = 1
LEDGER_CAPACITY = 3
LEDGER_MAX_ACTIONS = 3
LEDGER_MASTER_SEED = 1608
LEDGER_ATTEMPT_INDEX = 3
LEDGER_MAX_RNG_REJECTIONS = 64

LEDGER_SUITE_ID = 0x4C4544470001
LEDGER_BUGGY_NAMESPACE = 1
LEDGER_REPLAY_NAMESPACE = 3
LEDGER_TARGET_VALID_CASES = 4
LEDGER_MAX_DISCARDS = 0
LEDGER_MAX_SHRINK_EVALUATIONS = 18
LEDGER_MAX_STATE_EVALUATIONS = 22
LEDGER_MAX_DEPLOYMENTS = 66

LEDGER_SOURCE_BUNDLE_FINGERPRINT = int(
    "e7bf9de220a5c32c42ccba23fc5dae8f67c78c75bc3933f99a63073f1d9e98ee", 16
)
LEDGER_TOOLCHAIN_FINGERPRINT = int(
    "5aeb86a363465c7918ea97437c00f7f80f2863b4b8f7dad5edce728a3c8077a0", 16
)
LEDGER_ACTION_ENCODING_DOMAIN = b"FECHECK/ACCOUNTING-LEDGER/ACTION-ENCODING/V1"
LEDGER_MODEL_DOMAIN = b"FECHECK/ACCOUNTING-LEDGER/MODEL/V1"
LEDGER_FIXTURE_POLICY_DOMAIN = b"FECHECK/ACCOUNTING-LEDGER/FIXTURE-POLICY/V1"
LEDGER_FAILURE_SCHEMA_DOMAIN = b"FECHECK/ACCOUNTING-LEDGER/FAILURE-SCHEMA/V1"
LEDGER_SNAPSHOT_SCHEMA_DOMAIN = b"FECHECK/ACCOUNTING-LEDGER/SNAPSHOT-SCHEMA/V1"
LEDGER_ADAPTER_LOGIC_DOMAIN = b"FECHECK/ACCOUNTING-LEDGER/ADAPTER-LOGIC/V1"

ledger_action_encoding_hash = keccak256(LEDGER_ACTION_ENCODING_DOMAIN)
ledger_model_hash = keccak256(LEDGER_MODEL_DOMAIN)
ledger_fixture_policy_hash = keccak256(LEDGER_FIXTURE_POLICY_DOMAIN)
ledger_failure_schema_hash = keccak256(LEDGER_FAILURE_SCHEMA_DOMAIN)
ledger_snapshot_schema_hash = keccak256(LEDGER_SNAPSHOT_SCHEMA_DOMAIN)
ledger_adapter_logic_hash = keccak256(LEDGER_ADAPTER_LOGIC_DOMAIN)

LEDGER_ACTION_ENCODING_FINGERPRINT = as_int(ledger_action_encoding_hash)
LEDGER_MODEL_FINGERPRINT = as_int(ledger_model_hash)
LEDGER_FIXTURE_POLICY_FINGERPRINT = as_int(ledger_fixture_policy_hash)
LEDGER_FAILURE_SCHEMA_FINGERPRINT = as_int(ledger_failure_schema_hash)
LEDGER_SNAPSHOT_SCHEMA_FINGERPRINT = as_int(ledger_snapshot_schema_hash)
LEDGER_ADAPTER_LOGIC_FINGERPRINT = as_int(ledger_adapter_logic_hash)

LEDGER_SEMANTIC_DOMAINS = (
    ("action_encoding", LEDGER_ACTION_ENCODING_DOMAIN, ledger_action_encoding_hash),
    ("model", LEDGER_MODEL_DOMAIN, ledger_model_hash),
    ("fixture_policy", LEDGER_FIXTURE_POLICY_DOMAIN, ledger_fixture_policy_hash),
    ("failure_schema", LEDGER_FAILURE_SCHEMA_DOMAIN, ledger_failure_schema_hash),
    ("snapshot_schema", LEDGER_SNAPSHOT_SCHEMA_DOMAIN, ledger_snapshot_schema_hash),
    ("adapter_logic", LEDGER_ADAPTER_LOGIC_DOMAIN, ledger_adapter_logic_hash),
)
LEDGER_BUGGY_INIT_CODE_HASH = int(
    "7b5481653ad9044d751fb34c7505156e43a0d2a93a327b6b1561081cc028a063", 16
)
LEDGER_FIXED_INIT_CODE_HASH = int(
    "6f5b12aa8bef643d95412a7fb7df3628389d697d1186c9849d530f807e3fbec1", 16
)
LEDGER_ACTOR_INIT_CODE_TEMPLATE_HASH = int(
    "109f96d2218de4843ea2f21d4f8b93fc736477a549d26624216f368888863c21", 16
)
LEDGER_BUGGY_RUNTIME_CODE_HASH = int(
    "85638412d87d4195e2a475b23e0a803d8f669e9f23c653de2f6ca7f878487b5f", 16
)
LEDGER_FIXED_RUNTIME_CODE_HASH = int(
    "607330e267aa0dc7a423da5ae4d8c671fbb05ead67cbb6b977f1d1c3fdff8c21", 16
)
LEDGER_ACTOR_RUNTIME_CODE_HASH = int(
    "29a05393777217742bb4520ca4779be0ced3806b9c9d0ca6c0cee579a34290cf", 16
)


def stateful_word_preimage(domain: str, values: list[int]) -> bytes:
    """Mirror `keccak_words`: one padded ASCII domain word, then u256 words."""
    encoded_domain = domain.encode("ascii")
    if len(encoded_domain) > 32:
        raise ValueError("stateful word domain exceeds one word")
    return encoded_domain.ljust(32, b"\x00") + b"".join(u256(value) for value in values)


def hash_stateful_words(domain: str, values: list[int]) -> tuple[bytes, bytes]:
    payload = stateful_word_preimage(domain, values)
    return payload, keccak256(payload)


ledger_bounds_descriptor = as_int(
    keccak256(u256(LEDGER_LO) + u256(LEDGER_HI))
)
ledger_scalar_edges_descriptor = as_int(
    keccak256(
        u256(3)
        + u256(LEDGER_LO)
        + u256(LEDGER_ORIGIN)
        + u256(LEDGER_HI)
    )
)
ledger_scalar_preimage, ledger_scalar_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [
        1,
        ledger_bounds_descriptor,
        LEDGER_ORIGIN,
        0,
        0,
        0,
        ledger_scalar_edges_descriptor,
        1,
        1,
        1,
    ],
)

ledger_empty_hash = keccak256(encode_action_seq([]))
ledger_one_hash = keccak256(encode_action_seq([LEDGER_ORIGIN]))
ledger_three_hash = keccak256(
    encode_action_seq([LEDGER_ORIGIN, LEDGER_ORIGIN, LEDGER_ORIGIN])
)
ledger_sequence_edges_descriptor = as_int(
    keccak256(
        u256(3) + ledger_empty_hash + ledger_one_hash + ledger_three_hash
    )
)
ledger_sequence_preimage, ledger_sequence_hash = hash_word_fields(
    "FECHECK/STRATEGY/V1",
    [
        3,
        0,
        as_int(ledger_empty_hash),
        LEDGER_CAPACITY,
        LEDGER_MAX_ACTIONS,
        as_int(ledger_scalar_hash),
        ledger_sequence_edges_descriptor,
        1,
        1,
        1,
    ],
)
ledger_generation_preimage, ledger_generation_hash = hash_word_fields(
    "FECHECK/GENERATION/V1", [1, 1, as_int(ledger_sequence_hash)]
)
ledger_attempt_preimage, ledger_attempt_hash = hash_word_fields(
    "FECHECK/ATTEMPT/V1",
    [
        LEDGER_MASTER_SEED,
        LEDGER_ATTEMPT_INDEX,
        as_int(ledger_generation_hash),
    ],
)

ledger_draw0_preimage = ledger_attempt_hash
ledger_draw0_hash = keccak256(ledger_draw0_preimage)
ledger_draw1_preimage = ledger_draw0_hash
ledger_draw1_hash = keccak256(ledger_draw1_preimage)
ledger_draw2_preimage = ledger_draw1_hash
ledger_draw2_hash = keccak256(ledger_draw2_preimage)
ledger_draw3_preimage = ledger_draw2_hash
ledger_draw3_hash = keccak256(ledger_draw3_preimage)

ledger_run_preimage, ledger_run_hash = hash_word_fields(
    "FECHECK/RUN/V1",
    [
        as_int(ledger_generation_hash),
        LEDGER_SUITE_ID,
        LEDGER_BUGGY_NAMESPACE,
        LEDGER_TARGET_VALID_CASES,
        LEDGER_MAX_DISCARDS,
        LEDGER_MAX_SHRINK_EVALUATIONS,
        LEDGER_MAX_STATE_EVALUATIONS,
        LEDGER_MAX_DEPLOYMENTS,
        1,
        1,
        as_int(action_seq_codec_hash),
    ],
)

ledger_original_value_preimage = (
    encode_bytes(b"FECHECK/VALUE/V1")
    + u256(2)
    + field(1, ledger_sequence_hash)
    + field(2, encode_action_seq([2, 17, 25]))
)
ledger_original_value_hash = keccak256(ledger_original_value_preimage)
ledger_reduced_value_preimage = (
    encode_bytes(b"FECHECK/VALUE/V1")
    + u256(2)
    + field(1, ledger_sequence_hash)
    + field(2, encode_action_seq([1, 17]))
)
ledger_reduced_value_hash = keccak256(ledger_reduced_value_preimage)

ledger_protocol_preimage, ledger_protocol_hash = hash_stateful_words(
    "FECHECK/STATEFUL-PROTOCOL/V1", [1]
)
ledger_fixture_plan_preimage, ledger_fixture_plan_hash = hash_stateful_words(
    "FECHECK/STATEFUL-FIXTURE/V1", [3]
)


def ledger_adapter_values(target_init: int, target_runtime: int) -> list[int]:
    return [
        1,
        as_int(ledger_protocol_hash),
        as_int(ledger_fixture_plan_hash),
        LEDGER_FIXTURE_POLICY_FINGERPRINT,
        LEDGER_ACTION_ENCODING_FINGERPRINT,
        LEDGER_MODEL_FINGERPRINT,
        LEDGER_SNAPSHOT_SCHEMA_FINGERPRINT,
        LEDGER_FAILURE_SCHEMA_FINGERPRINT,
        LEDGER_ADAPTER_LOGIC_FINGERPRINT,
        target_init,
        LEDGER_ACTOR_INIT_CODE_TEMPLATE_HASH,
        target_runtime,
        LEDGER_ACTOR_RUNTIME_CODE_HASH,
        LEDGER_SOURCE_BUNDLE_FINGERPRINT,
        LEDGER_TOOLCHAIN_FINGERPRINT,
    ]


ledger_buggy_adapter_values = ledger_adapter_values(
    LEDGER_BUGGY_INIT_CODE_HASH, LEDGER_BUGGY_RUNTIME_CODE_HASH
)
ledger_fixed_adapter_values = ledger_adapter_values(
    LEDGER_FIXED_INIT_CODE_HASH, LEDGER_FIXED_RUNTIME_CODE_HASH
)
ledger_buggy_adapter_preimage, ledger_buggy_adapter_hash = hash_stateful_words(
    "FECHECK/STATEFUL-ADAPTER/V1", ledger_buggy_adapter_values
)
ledger_fixed_adapter_preimage, ledger_fixed_adapter_hash = hash_stateful_words(
    "FECHECK/STATEFUL-ADAPTER/V1", ledger_fixed_adapter_values
)
ledger_bound_run_preimage, ledger_bound_run_hash = hash_stateful_words(
    "FECHECK/STATEFUL-RUN/V1",
    [
        as_int(ledger_run_hash),
        as_int(ledger_buggy_adapter_hash),
        LEDGER_FIXTURE_POLICY_FINGERPRINT,
    ],
)
ledger_original_execution_preimage, ledger_original_execution_hash = hash_stateful_words(
    "FECHECK/EXEC-ORIGINAL/V1",
    [as_int(ledger_bound_run_hash), LEDGER_BUGGY_NAMESPACE],
)

ledger_capsule_words = [
    as_int(b"FECHECK/STATEFUL/CAPSULE/V1".ljust(32, b"\x00")),
    36,
    1,
    1,
    1,
    as_int(ledger_protocol_hash),
    LEDGER_FIXTURE_POLICY_FINGERPRINT,
    LEDGER_CAPACITY,
    LEDGER_SUITE_ID,
    LEDGER_BUGGY_NAMESPACE,
    LEDGER_MASTER_SEED,
    LEDGER_ATTEMPT_INDEX,
    as_int(ledger_attempt_hash),
    as_int(ledger_generation_hash),
    as_int(ledger_run_hash),
    as_int(ledger_bound_run_hash),
    as_int(ledger_buggy_adapter_hash),
    0x4C45444701,
    1,
    0,
    as_int(ledger_original_value_hash),
    as_int(ledger_reduced_value_hash),
    4,
    3,
    0,
    22,
    22,
    66,
    21,
    18,
    2,
    8,
    8,
    0,
    0,
]
ledger_capsule_preimage = b"".join(u256(word) for word in ledger_capsule_words)
ledger_capsule_hash = keccak256(ledger_capsule_preimage)
ledger_capsule_wire = ledger_capsule_preimage + ledger_capsule_hash
ledger_replay_execution_preimage, ledger_replay_execution_hash = hash_stateful_words(
    "FECHECK/EXEC-REPLAY/V1",
    [
        as_int(ledger_bound_run_hash),
        as_int(ledger_capsule_hash),
        LEDGER_REPLAY_NAMESPACE,
    ],
)


def stateful_capsule_wire_is_valid(wire: bytes) -> bool:
    """Check the V1 exact length and its self-excluding final digest word."""
    return len(wire) == 1152 and keccak256(wire[:-32]) == wire[-32:]


LEDGER_HASH_VECTORS = {
    "accounting_ledger_scalar_strategy": (
        ledger_scalar_preimage,
        ledger_scalar_hash,
        "d2ea76fb4727d2d963519393fbd3da268fefd347649838588a14f0733cb38135",
    ),
    "accounting_ledger_sequence_strategy": (
        ledger_sequence_preimage,
        ledger_sequence_hash,
        "6ae4aa2ef26a8849817c65b1076ba384ca37d5dc5411c5ea95e0e149669f2a43",
    ),
    "accounting_ledger_generation": (
        ledger_generation_preimage,
        ledger_generation_hash,
        "f725d808dea501290fa02d43b07786393c747a511c813d737ec264f40daed6f7",
    ),
    "accounting_ledger_attempt": (
        ledger_attempt_preimage,
        ledger_attempt_hash,
        "16f357ec6dd0976b09f8a1e1892f60262163fb2493a5bf9e03c71903f4659097",
    ),
    "accounting_ledger_draw0": (
        ledger_draw0_preimage,
        ledger_draw0_hash,
        "ecf88291f6935adb138233cd1e9d049e572de22ac4e75caf0f43f7ba139b65ef",
    ),
    "accounting_ledger_draw1": (
        ledger_draw1_preimage,
        ledger_draw1_hash,
        "7deb7431205d73a50845c138366256954d607bec46ab02a07ca640afc75ac4ad",
    ),
    "accounting_ledger_draw2": (
        ledger_draw2_preimage,
        ledger_draw2_hash,
        "9e269d60b46410b560c6caa6c4231993cd2610753c1218396e9529605e338036",
    ),
    "accounting_ledger_draw3": (
        ledger_draw3_preimage,
        ledger_draw3_hash,
        "8a201bc8b5b568757a7a5ea7afbcc934f9536b572c85a0c78c158cfc8350b58e",
    ),
    "accounting_ledger_action_encoding": (
        LEDGER_ACTION_ENCODING_DOMAIN,
        ledger_action_encoding_hash,
        "67d58f903806ee40c34cff6cb13414aecfb3683f94ddbaaf7496035d09070625",
    ),
    "accounting_ledger_model": (
        LEDGER_MODEL_DOMAIN,
        ledger_model_hash,
        "c1423a868084918f2457dd0d09e75633e135e7b35a854e6bd8dbc65e0815d926",
    ),
    "accounting_ledger_fixture_policy": (
        LEDGER_FIXTURE_POLICY_DOMAIN,
        ledger_fixture_policy_hash,
        "8428790e9e9db5de5013ff9db9c9d0f450be0d86247c34bf4854b380c858105a",
    ),
    "accounting_ledger_failure_schema": (
        LEDGER_FAILURE_SCHEMA_DOMAIN,
        ledger_failure_schema_hash,
        "65242bbd8ded40b90e37ff842f83ccb18bc65bd14242bbd1146fbeeffc5983f0",
    ),
    "accounting_ledger_snapshot_schema": (
        LEDGER_SNAPSHOT_SCHEMA_DOMAIN,
        ledger_snapshot_schema_hash,
        "6d5686d6260d162552aba0c3e17bd7585c780e6cbcdf30197f09fd3c3c562724",
    ),
    "accounting_ledger_adapter_logic": (
        LEDGER_ADAPTER_LOGIC_DOMAIN,
        ledger_adapter_logic_hash,
        "6c95e6a147705c2a687d04bf122d69fa31d756405b7d8d9616fad2dee7e11e56",
    ),
    "accounting_ledger_run": (
        ledger_run_preimage,
        ledger_run_hash,
        "edc064b8116a6def4ef7a8c49f3801a909a90d7007ad08e0443415c4cb5678e2",
    ),
    "accounting_ledger_original_value": (
        ledger_original_value_preimage,
        ledger_original_value_hash,
        "6e62a2972970be70cf7e1196ad1fc9c0594cf5553c801705ac44139677989a4f",
    ),
    "accounting_ledger_reduced_value": (
        ledger_reduced_value_preimage,
        ledger_reduced_value_hash,
        "fb7dfe56f9f0dcfd649005d929177699c1edfb58ec19e81a90adb8a24cef0f2e",
    ),
    "accounting_ledger_stateful_protocol": (
        ledger_protocol_preimage,
        ledger_protocol_hash,
        "c79098012a110203d44db589835ef53d508b3631ca34432c109ce1c0f65f9c59",
    ),
    "accounting_ledger_stateful_fixture_plan": (
        ledger_fixture_plan_preimage,
        ledger_fixture_plan_hash,
        "9d3f8baf2a94f15ffbf65420ddd54bc32f46b0d6672ef0a410d45e6ddd1fbac9",
    ),
    "accounting_ledger_buggy_adapter": (
        ledger_buggy_adapter_preimage,
        ledger_buggy_adapter_hash,
        "074365e010d55b454bda6cffd10c9fd83f62290417f5581a6dd6f132835d8d7f",
    ),
    "accounting_ledger_fixed_adapter": (
        ledger_fixed_adapter_preimage,
        ledger_fixed_adapter_hash,
        "772a61646078d996bd683a17f541c91ea2969e17afcbac0397937d2c4889e930",
    ),
    "accounting_ledger_bound_run": (
        ledger_bound_run_preimage,
        ledger_bound_run_hash,
        "69f5e944243cae3a6d2568006c31fd07b183d55e5747960e508a94db509779ec",
    ),
    "accounting_ledger_original_execution": (
        ledger_original_execution_preimage,
        ledger_original_execution_hash,
        "d8759fd98c87d828e1b7497c3e2118105885b49c53eca3eb9d46c1f3324d6fff",
    ),
    "accounting_ledger_bound_capsule": (
        ledger_capsule_preimage,
        ledger_capsule_hash,
        "00631848a15b7b3a045f41b45002725bb7ac460ec9a5e76be88e3a3b229ebe45",
    ),
    "accounting_ledger_replay_execution": (
        ledger_replay_execution_preimage,
        ledger_replay_execution_hash,
        "fb5bf10a0a82085365c91024ca408259a08a3673bd91ee6413082803aae8e128",
    ),
}


def ledger_uniform(state: bytes, upper: int) -> tuple[bytes, int]:
    """Mirror KeccakRng.uniform, including rejection of modulo-biased words."""
    threshold = (1 << 256) % upper
    for _ in range(LEDGER_MAX_RNG_REJECTIONS):
        state = keccak256(state)
        word = as_int(state)
        if word >= threshold:
            return state, word % upper
    raise AssertionError("AccountingLedger RNG exceeded the V1 rejection cap")


def ledger_attempt(attempt_index: int) -> tuple[list[int], list[int], list[bytes]]:
    if attempt_index == 0:
        return [], [], []
    if attempt_index == 1:
        return [LEDGER_ORIGIN], [], []
    if attempt_index == 2:
        return [LEDGER_ORIGIN] * LEDGER_MAX_ACTIONS, [], []

    _, seed = hash_word_fields(
        "FECHECK/ATTEMPT/V1",
        [LEDGER_MASTER_SEED, attempt_index, as_int(ledger_generation_hash)],
    )
    draws = []
    reduced = []
    seed, logical_len = ledger_uniform(seed, LEDGER_MAX_ACTIONS + 1)
    draws.append(seed)
    reduced.append(logical_len)
    physical = []
    for _ in range(LEDGER_CAPACITY):
        seed, action = ledger_uniform(seed, LEDGER_HI - LEDGER_LO + 1)
        draws.append(seed)
        reduced.append(action)
        physical.append(action)
    return physical[:logical_len], reduced, draws


def decode_ledger_action(word: int) -> tuple[str, int, int, int] | None:
    if word < LEDGER_LO or word > LEDGER_HI:
        return None
    amount = word & 0x3
    actor = (word >> 2) & 0x1
    recipient = (word >> 3) & 0x1
    kind = (word >> 4) & 0x1
    if amount == 3:
        return None
    if kind == 0:
        if recipient != 0:
            return None
        return "deposit", actor, actor, amount
    return "transfer", actor, recipient, amount


def evaluate_ledger(
    actions: list[int], *, fixed: bool = False
) -> tuple[str, int]:
    """Pure reference model plus an independent buggy/fixed target simulation."""
    model = [0, 0, 0]
    target = [0, 0, 0]
    executed = 0

    for word in actions:
        action = decode_ledger_action(word)
        if action is None:
            return "D", executed
        kind, source, recipient, amount = action
        if amount == 0:
            return "D", executed
        if kind == "transfer" and model[source] < amount:
            return "D", executed

        predicted = model.copy()
        if kind == "deposit":
            predicted[source] += amount
            predicted[2] += amount
            target[source] += amount
            target[2] += amount
        else:
            if source != recipient:
                predicted[source] -= amount
                predicted[recipient] += amount

            if not (fixed and source == recipient):
                source_before = target[source]
                recipient_before = target[recipient]
                target[source] = source_before - amount
                target[recipient] = recipient_before + amount

        executed += 1
        if target[2] != target[0] + target[1]:
            return "F", executed
        if target != predicted:
            return "K", executed
        model = predicted

    return "P", executed


def scalar_shrink_candidates(origin: int, current: int):
    distance = abs(current - origin)
    if distance == 0:
        return
    yield origin
    if distance == 1:
        return

    step = distance // 2 + distance % 2
    while step != 0:
        if current > origin:
            yield current - step
        else:
            yield current + step
        if step == 1:
            return
        step = step // 2 + step % 2


def ledger_shrink_candidates(actions: list[int]):
    length = len(actions)
    for block_len in range(length, 0, -1):
        seen = set()
        for start in range(0, length - block_len + 1):
            candidate = actions[:start] + actions[start + block_len :]
            key = tuple(candidate)
            if key in seen:
                continue
            seen.add(key)
            yield candidate

    for index, word in enumerate(actions):
        for candidate_word in scalar_shrink_candidates(LEDGER_ORIGIN, word):
            candidate = actions.copy()
            candidate[index] = candidate_word
            yield candidate


def shrink_ledger(original: list[int]):
    failure, _ = evaluate_ledger(original)
    if failure != "F":
        raise AssertionError("AccountingLedger original does not falsify conservation")

    current = original.copy()
    trace = []
    counters = {
        "evaluations": 0,
        "accepted": 0,
        "rejected_pass": 0,
        "rejected_discard": 0,
        "rejected_failure_key": 0,
    }
    actions_executed = 0

    while True:
        accepted = False
        for candidate in ledger_shrink_candidates(current):
            verdict, executed = evaluate_ledger(candidate)
            trace.append((candidate, verdict))
            counters["evaluations"] += 1
            actions_executed += executed
            if verdict == failure:
                counters["accepted"] += 1
                current = candidate
                accepted = True
                break
            if verdict == "P":
                counters["rejected_pass"] += 1
            elif verdict == "D":
                counters["rejected_discard"] += 1
            else:
                counters["rejected_failure_key"] += 1
        if not accepted:
            return current, trace, counters, actions_executed


LEDGER_EXPECTED_TRACE = [
    ([], "P"),
    ([25], "D"),
    ([2], "P"),
    ([17, 25], "D"),
    ([2, 25], "P"),
    ([2, 17], "F"),
    ([], "P"),
    ([17], "D"),
    ([2], "P"),
    ([1, 17], "F"),
    ([], "P"),
    ([17], "D"),
    ([1], "P"),
    ([1, 1], "P"),
    ([1, 9], "D"),
    ([1, 13], "D"),
    ([1, 15], "D"),
    ([1, 16], "D"),
]

VECTORS = {
    "fixture": (
        fixture_preimage,
        fixture_hash,
        "b05382ae85f59ba83741fd249973c169fe353b27479f9b0136e8db06b795912b",
    ),
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
    "action_seq_random_attempt4": (
        action_seq_random_attempt4_preimage,
        action_seq_random_attempt4_hash,
        "beda1fdf94f0aa894e68e6db5f378d60e036c7128e0aacc3784be6d36809449c",
    ),
    "action_seq_random4_word0": (
        action_seq_random4_word0_preimage,
        action_seq_random4_word0_hash,
        "2ac8a745367868e8bb59e00f985c1d1a5d556f0d316e9d1407e9879c248a9787",
    ),
    "action_seq_random4_word1": (
        action_seq_random4_word1_preimage,
        action_seq_random4_word1_hash,
        "58c3ab1ef741084ac6da3d607903ccecc228594f7e0f10dfa21b10ab798db4f9",
    ),
    "action_seq_random4_word2": (
        action_seq_random4_word2_preimage,
        action_seq_random4_word2_hash,
        "9d6402469402e13565fffef60f8ed17fc8b83308fbf303f5cc7b2d62fee5db63",
    ),
    "action_seq_random4_word3": (
        action_seq_random4_word3_preimage,
        action_seq_random4_word3_hash,
        "4c7adfba5d34ac07cb86f5daa18278437735b7824ad2ad8648a5cbe532b02adf",
    ),
    "action_seq_random4_value": (
        action_seq_random4_value_preimage,
        action_seq_random4_value_hash,
        "e0f704e3c6fd08a45108b36d3bec277bdfddbea47455cc2dd25573f471801867",
    ),
    "action_seq_run": (
        action_seq_run_preimage,
        action_seq_run_hash,
        "64ffc2dba5d425a82182294b4cf8501934820f18170611ea948b1d286f566a5b",
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


def verify_accounting_ledger_vectors() -> None:
    for name, (payload, digest, expected_hex) in LEDGER_HASH_VECTORS.items():
        actual_hex = digest.hex()
        if actual_hex != expected_hex:
            raise AssertionError(f"{name}: expected {expected_hex}, got {actual_hex}")
        print(f"{name}.preimage.len={len(payload)}")
        print(f"{name}.preimage.hex={payload.hex()}")
        print(f"{name}.keccak256=0x{actual_hex}")

    if len(LEDGER_HASH_VECTORS) != 25:
        raise AssertionError(
            f"expected 25 AccountingLedger hash vectors, got {len(LEDGER_HASH_VECTORS)}"
        )
    for name, domain, digest in LEDGER_SEMANTIC_DOMAINS:
        if domain.endswith(b"\x00"):
            raise AssertionError(f"{name} semantic domain contains a trailing NUL")
        if keccak256(domain + b"\x00") == digest:
            raise AssertionError(
                f"{name} semantic fingerprint failed to distinguish a trailing NUL"
            )

    if len(ledger_capsule_words) != 35:
        raise AssertionError("stateful capsule payload must contain exactly 35 words")
    if len(ledger_capsule_wire) != 1152:
        raise AssertionError("stateful capsule wire must contain exactly 1152 bytes")
    if ledger_capsule_wire[:-32] != ledger_capsule_preimage:
        raise AssertionError("stateful capsule wire payload changed")
    if ledger_capsule_wire[-32:] != ledger_capsule_hash:
        raise AssertionError("stateful capsule wire digest word changed")

    if not stateful_capsule_wire_is_valid(ledger_capsule_wire):
        raise AssertionError("canonical stateful capsule wire was rejected")
    if stateful_capsule_wire_is_valid(ledger_capsule_wire[:-1]):
        raise AssertionError("truncated stateful capsule wire was accepted")
    if stateful_capsule_wire_is_valid(ledger_capsule_wire + b"\x00"):
        raise AssertionError("stateful capsule wire with trailing data was accepted")

    for index in range(len(ledger_capsule_words)):
        mutated_wire = bytearray(ledger_capsule_wire)
        mutated_wire[index * 32 + 31] ^= 1
        if stateful_capsule_wire_is_valid(bytes(mutated_wire)):
            raise AssertionError(f"capsule word mutation {index} was accepted")
    digest_mutation = bytearray(ledger_capsule_wire)
    digest_mutation[-1] ^= 1
    if stateful_capsule_wire_is_valid(bytes(digest_mutation)):
        raise AssertionError("capsule digest mutation was accepted")

    for index in range(len(ledger_buggy_adapter_values)):
        mutated = ledger_buggy_adapter_values.copy()
        mutated[index] ^= 1
        _, mutated_digest = hash_stateful_words(
            "FECHECK/STATEFUL-ADAPTER/V1", mutated
        )
        if mutated_digest == ledger_buggy_adapter_hash:
            raise AssertionError(f"adapter field mutation {index} was not bound")

    if ledger_fixed_adapter_hash == ledger_buggy_adapter_hash:
        raise AssertionError("buggy and fixed adapter identities must differ")
    _, changed_bound = hash_stateful_words(
        "FECHECK/STATEFUL-RUN/V1",
        [
            as_int(ledger_run_hash),
            as_int(ledger_buggy_adapter_hash),
            LEDGER_FIXTURE_POLICY_FINGERPRINT ^ 1,
        ],
    )
    if changed_bound == ledger_bound_run_hash:
        raise AssertionError("fixture-policy mutation was not bound")
    _, changed_replay = hash_stateful_words(
        "FECHECK/EXEC-REPLAY/V1",
        [as_int(ledger_bound_run_hash), as_int(ledger_capsule_hash), 4],
    )
    if changed_replay == ledger_replay_execution_hash:
        raise AssertionError("replay namespace mutation was not bound")

    reserved = [
        word
        for word in range(LEDGER_LO, LEDGER_HI + 1)
        if decode_ledger_action(word) is None
    ]
    expected_reserved = [3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 19, 23, 27]
    if reserved != expected_reserved:
        raise AssertionError(
            f"AccountingLedger reserved words: expected {expected_reserved}, got {reserved}"
        )
    canonical = [
        decode_ledger_action(word)
        for word in range(LEDGER_LO, LEDGER_HI + 1)
        if decode_ledger_action(word) is not None
    ]
    if len(canonical) != 18:
        raise AssertionError(
            f"AccountingLedger canonical domain: expected 18 actions, got {len(canonical)}"
        )
    if sum(action[3] == 0 for action in canonical) != 6:
        raise AssertionError("AccountingLedger must have six canonical zero actions")

    original, reduced_draws, raw_draws = ledger_attempt(LEDGER_ATTEMPT_INDEX)
    expected_raw_draws = [
        ledger_draw0_hash,
        ledger_draw1_hash,
        ledger_draw2_hash,
        ledger_draw3_hash,
    ]
    if raw_draws != expected_raw_draws:
        raise AssertionError("AccountingLedger RNG chain differs from its golden")
    if reduced_draws != [3, 2, 17, 25]:
        raise AssertionError(
            f"AccountingLedger reduced draws: expected [3, 2, 17, 25], "
            f"got {reduced_draws}"
        )
    if original != [2, 17, 25]:
        raise AssertionError(
            f"AccountingLedger original: expected [2, 17, 25], got {original}"
        )
    original_semantics = [decode_ledger_action(word) for word in original]
    expected_semantics = [
        ("deposit", 0, 0, 2),
        ("transfer", 0, 0, 1),
        ("transfer", 0, 1, 1),
    ]
    if original_semantics != expected_semantics:
        raise AssertionError(
            f"AccountingLedger original semantics changed: {original_semantics}"
        )

    original_attempts = [ledger_attempt(index)[0] for index in range(4)]
    if original_attempts != [[], [1], [1, 1, 1], [2, 17, 25]]:
        raise AssertionError(
            f"AccountingLedger attempts 0..3 changed: {original_attempts}"
        )
    original_results = [evaluate_ledger(value) for value in original_attempts]
    if original_results != [("P", 0), ("P", 1), ("P", 3), ("F", 2)]:
        raise AssertionError(
            f"AccountingLedger original accounting changed: {original_results}"
        )

    minimal, trace, shrink, shrink_actions = shrink_ledger(original)
    if minimal != [1, 17]:
        raise AssertionError(
            f"AccountingLedger minimal: expected [1, 17], got {minimal}"
        )
    if trace != LEDGER_EXPECTED_TRACE:
        raise AssertionError(
            f"AccountingLedger shrink trace changed:\nexpected={LEDGER_EXPECTED_TRACE}\n"
            f"actual={trace}"
        )
    expected_shrink = {
        "evaluations": 18,
        "accepted": 2,
        "rejected_pass": 8,
        "rejected_discard": 8,
        "rejected_failure_key": 0,
    }
    if shrink != expected_shrink:
        raise AssertionError(
            f"AccountingLedger shrink counters: expected {expected_shrink}, got {shrink}"
        )
    if shrink_actions != 15:
        raise AssertionError(
            f"AccountingLedger shrink actions: expected 15, got {shrink_actions}"
        )
    total_actions = sum(executed for _, executed in original_results) + shrink_actions
    if total_actions != 21:
        raise AssertionError(
            f"AccountingLedger total actions: expected 21, got {total_actions}"
        )
    buggy_stats = {
        "attempts": len(original_attempts),
        "valid_cases": sum(verdict == "P" for verdict, _ in original_results),
        "discards": sum(verdict == "D" for verdict, _ in original_results),
        "property_evaluations": len(original_attempts) + shrink["evaluations"],
        "fixture_evaluations": len(original_attempts) + shrink["evaluations"],
        "contract_deployments": 3
        * (len(original_attempts) + shrink["evaluations"]),
        "actions_executed": total_actions,
    }
    expected_buggy_stats = {
        "attempts": 4,
        "valid_cases": 3,
        "discards": 0,
        "property_evaluations": 22,
        "fixture_evaluations": 22,
        "contract_deployments": 66,
        "actions_executed": 21,
    }
    if buggy_stats != expected_buggy_stats:
        raise AssertionError(
            f"AccountingLedger buggy stats: expected {expected_buggy_stats}, got {buggy_stats}"
        )

    fixed_results = [
        evaluate_ledger(value, fixed=True) for value in original_attempts
    ]
    if fixed_results != [("P", 0), ("P", 1), ("P", 3), ("P", 3)]:
        raise AssertionError(
            f"AccountingLedger fixed comparison changed: {fixed_results}"
        )
    fixed_stats = {
        "attempts": len(original_attempts),
        "valid_cases": sum(verdict == "P" for verdict, _ in fixed_results),
        "discards": sum(verdict == "D" for verdict, _ in fixed_results),
        "property_evaluations": len(original_attempts),
        "fixture_evaluations": len(original_attempts),
        "contract_deployments": 3 * len(original_attempts),
        "actions_executed": sum(executed for _, executed in fixed_results),
    }
    expected_fixed_stats = {
        "attempts": 4,
        "valid_cases": 4,
        "discards": 0,
        "property_evaluations": 4,
        "fixture_evaluations": 4,
        "contract_deployments": 12,
        "actions_executed": 7,
    }
    if fixed_stats != expected_fixed_stats:
        raise AssertionError(
            f"AccountingLedger fixed stats: expected {expected_fixed_stats}, got {fixed_stats}"
        )

    print(f"accounting_ledger.reserved={reserved}")
    print(f"accounting_ledger.draws.mod={reduced_draws}")
    print(f"accounting_ledger.original={original}")
    print(f"accounting_ledger.minimal={minimal}")
    print(f"accounting_ledger.trace={trace}")
    print(f"accounting_ledger.shrink={shrink}")
    print(f"accounting_ledger.original_stats={buggy_stats}")
    print(f"accounting_ledger.fixed_stats={fixed_stats}")


def main() -> None:
    if len(VECTORS) != 32:
        raise AssertionError(
            f"expected the 32 pre-C6a vectors to remain intact, got {len(VECTORS)}"
        )
    for name, (payload, digest, expected_hex) in VECTORS.items():
        actual_hex = digest.hex()
        if actual_hex != expected_hex:
            raise AssertionError(f"{name}: expected {expected_hex}, got {actual_hex}")
        print(f"{name}.preimage.len={len(payload)}")
        print(f"{name}.preimage.hex={payload.hex()}")
        print(f"{name}.keccak256=0x{actual_hex}")

    verify_accounting_ledger_vectors()


if __name__ == "__main__":
    main()
