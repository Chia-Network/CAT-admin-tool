from cats.secure_the_bag import batch_the_bag, secure_the_bag, Target

from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.condition_opcodes import ConditionOpcode
from chia.util.ints import uint64

def test_batch_the_bag():
    targets = [
        Target(
            bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba"),
            uint64(10000000000000000)
        ),
        Target(
            bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c"),
            uint64(32100000000)
        ),
        Target(
            bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4"),
            uint64(10000000000000000)
        )
    ]
    results = batch_the_bag(targets, 2)

    assert len(results) == 2
    assert len(results[0]) == 2
    assert len(results[1]) == 1

    assert results[0][0].puzzle_hash == bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    assert results[0][0].amount == uint64(10000000000000000)

    assert results[0][1].puzzle_hash == bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    assert results[0][1].amount == uint64(32100000000)

    assert results[1][0].puzzle_hash == bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4")
    assert results[1][0].amount == uint64(10000000000000000)

def test_batch_the_bag_puzzle_hash_amount_collision():
    targets = [
        Target(
            bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba"),
            uint64(10000000000000000)
        ),
        Target(
            bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba"),
            uint64(10000000000000000)
        ),
        Target(
            bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c"),
            uint64(32100000000)
        ),
        Target(
            bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4"),
            uint64(10000000000000000)
        )
    ]
    results = batch_the_bag(targets, 2)

    assert len(results) == 2
    assert len(results[0]) == 2
    assert len(results[1]) == 2

    assert results[0][0].puzzle_hash == bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    assert results[0][0].amount == uint64(10000000000000000)

    assert results[0][1].puzzle_hash == bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    assert results[0][1].amount == uint64(32100000000)

    assert results[1][0].puzzle_hash == bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    assert results[1][0].amount == uint64(10000000000000000)

    assert results[1][1].puzzle_hash == bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4")
    assert results[1][1].amount == uint64(10000000000000000)

def test_batch_the_bag_puzzle_hash_amount_multiple_collisions():
    targets = [
        Target(
            bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba"),
            uint64(10000000000000000)
        ),
        Target(
            bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba"),
            uint64(10000000000000000)
        ),
        Target(
            bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba"),
            uint64(10000000000000000)
        ),
        Target(
            bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba"),
            uint64(10000000000000000)
        ),
        Target(
            bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c"),
            uint64(32100000000)
        ),
        Target(
            bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c"),
            uint64(32100000000)
        ),
        Target(
            bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c"),
            uint64(32100000000)
        ),
        Target(
            bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4"),
            uint64(10000000000000000)
        )
    ]
    results = batch_the_bag(targets, 2)

    assert len(results) == 4
    assert len(results[0]) == 2
    assert len(results[1]) == 2
    assert len(results[2]) == 2
    assert len(results[3]) == 2

    assert results[0][0].puzzle_hash == bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    assert results[0][0].amount == uint64(10000000000000000)

    assert results[0][1].puzzle_hash == bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    assert results[0][1].amount == uint64(32100000000)

    assert results[1][0].puzzle_hash == bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    assert results[1][0].amount == uint64(10000000000000000)

    assert results[1][1].puzzle_hash == bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    assert results[1][1].amount == uint64(32100000000)

    assert results[2][0].puzzle_hash == bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    assert results[2][0].amount == uint64(10000000000000000)

    assert results[2][1].puzzle_hash == bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    assert results[2][1].amount == uint64(32100000000)

    assert results[3][0].puzzle_hash == bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    assert results[3][0].amount == uint64(10000000000000000)

    assert results[3][1].puzzle_hash == bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4")
    assert results[3][1].amount == uint64(10000000000000000)

def test_secure_the_bag():
    target_1_puzzle_hash = bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    target_1_amount = uint64(10000000000000000)
    target_2_puzzle_hash = bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    target_2_amount = uint64(32100000000)
    target_3_puzzle_hash = bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4")
    target_3_amount = uint64(10000000000000000)

    targets = [
        Target(target_1_puzzle_hash, target_1_amount),
        Target(target_2_puzzle_hash, target_2_amount),
        Target(target_3_puzzle_hash, target_3_amount)
    ]
    root_hash, parent_puzzle_lookup = secure_the_bag(targets, 2)

    # Calculates correct root hash
    assert root_hash.hex() == "bbffed16fdfe5b4c79fced8d04d913a68ea4a028e843e4fb09df18d432713810"

    node_1_puzzle_hash = bytes32.fromhex("59e9003d6199915750187188a631187d0bb78b32a1ae04155615cae267975b4b")
    node_1_amount = uint64(10000032100000000)
    node_2_puzzle_hash = bytes32.fromhex("db49cd4d6507dada1f3407ebda46586d5254f8f29bbe6d360ef1b87a4c3100f8")
    node_2_amount = uint64(10000000000000000)

    root_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, None],
                [
                    ConditionOpcode.CREATE_COIN,
                    node_1_puzzle_hash,
                    node_1_amount,
                    [node_1_puzzle_hash]
                ],
                [
                    ConditionOpcode.CREATE_COIN,
                    node_2_puzzle_hash,
                    node_2_amount,
                    [node_2_puzzle_hash]
                ]
            ]
        )
    )

    # Puzzle reveal for root hash is correct
    assert root_puzzle.get_tree_hash().hex() == root_hash.hex()

    r = root_puzzle.run(0)

    expected_result = Program.to([
        [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, None],
        [ConditionOpcode.CREATE_COIN, node_1_puzzle_hash, node_1_amount, [node_1_puzzle_hash]],
        [ConditionOpcode.CREATE_COIN, node_2_puzzle_hash, node_2_amount, [node_2_puzzle_hash]]
    ])

    # Result of running root is correct
    assert r.get_tree_hash().hex() == expected_result.get_tree_hash().hex()

    node_1_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, None],
                [ConditionOpcode.CREATE_COIN, target_1_puzzle_hash, target_1_amount, [target_1_puzzle_hash]],
                [ConditionOpcode.CREATE_COIN, target_2_puzzle_hash, target_2_amount, [target_2_puzzle_hash]]
            ]
        )
    )

    # Puzzle reveal for node 1 is correct
    assert node_1_puzzle.get_tree_hash().hex() == node_1_puzzle_hash.hex()

    r = node_1_puzzle.run(0)

    expected_result = Program.to([
        [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, None],
        [ConditionOpcode.CREATE_COIN, target_1_puzzle_hash, target_1_amount, [target_1_puzzle_hash]],
        [ConditionOpcode.CREATE_COIN, target_2_puzzle_hash, target_2_amount, [target_2_puzzle_hash]]
    ])

    # Result of running node 1 is correct
    assert r.get_tree_hash().hex() == expected_result.get_tree_hash().hex()

    node_2_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, None],
                [ConditionOpcode.CREATE_COIN, target_3_puzzle_hash, target_3_amount, [target_3_puzzle_hash]]
            ]
        )
    )

    # Puzzle reveal for node 2 is correct
    assert node_2_puzzle.get_tree_hash().hex() == node_2_puzzle_hash.hex()

    r = node_2_puzzle.run(0)

    expected_result = Program.to([
        [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, None],
        [ConditionOpcode.CREATE_COIN, target_3_puzzle_hash, target_3_amount, [target_3_puzzle_hash]]
    ])

    # Result of running node 2 is correct
    assert r.get_tree_hash().hex() == expected_result.get_tree_hash().hex()

    # Parent puzzle lookup (used for puzzle reveals)

    puzzle_create_target_1 = parent_puzzle_lookup.get(target_1_puzzle_hash.hex())
    puzzle_create_target_2 = parent_puzzle_lookup.get(target_2_puzzle_hash.hex())
    puzzle_create_target_3 = parent_puzzle_lookup.get(target_3_puzzle_hash.hex())

    # Targets 1 & 2 are created by node 1
    assert puzzle_create_target_1.get_tree_hash().hex() == node_1_puzzle_hash.hex()
    assert puzzle_create_target_2.get_tree_hash().hex() == node_1_puzzle_hash.hex()

    # Target 3 is created by node 2
    assert puzzle_create_target_3.get_tree_hash().hex() == node_2_puzzle_hash.hex()

    puzzle_create_node_1 = parent_puzzle_lookup.get(node_1_puzzle_hash.hex())
    puzzle_create_node_2 = parent_puzzle_lookup.get(node_2_puzzle_hash.hex())

    # Nodes 1 & 2 are created by root
    assert puzzle_create_node_1.get_tree_hash().hex() == root_hash.hex()
    assert puzzle_create_node_2.get_tree_hash().hex() == root_hash.hex()
