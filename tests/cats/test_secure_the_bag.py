import pytest

from cats.secure_the_bag import batch_the_bag, parent_of_puzzle_hash, read_secure_the_bag_targets, secure_the_bag, Target

from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.condition_opcodes import ConditionOpcode
from chia.util.hash import std_hash
from chia.util.ints import uint64
from chia.wallet.cat_wallet.cat_utils import construct_cat_puzzle
from chia.wallet.puzzles.cat_loader import CAT_MOD
from clvm.casts import int_to_bytes

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

def test_secure_the_bag():
    target_1_puzzle_hash = bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    target_1_amount = uint64(10000000000000000)
    target_2_puzzle_hash = bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    target_2_amount = uint64(32100000000)
    target_3_puzzle_hash = bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4")
    target_3_amount = uint64(10000000000000000)

    targets = [
        Target(
            target_1_puzzle_hash,
            target_1_amount
        ),
        Target(
            target_2_puzzle_hash,
            target_2_amount
        ),
        Target(
            target_3_puzzle_hash,
            target_3_amount
        )
    ]
    root_hash, parent_puzzle_lookup = secure_the_bag(targets, 2)

    # Calculates correct root hash
    assert root_hash.hex() == "2a21783e7b1f5ab453e45315a35c1e02c4dd7234f3f41d2d64541819431d049d"

    node_1_puzzle_hash = bytes32.fromhex("f2cff3b95ddbaa61a214220d67a20901c584ff16df12ec769844f391d513835c")
    node_2_puzzle_hash = bytes32.fromhex("f45579725598a28c5572d8c534be3edf095830de0f984f0eb3d9bb251c71134b")

    root_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
                [
                    ConditionOpcode.CREATE_COIN,
                    node_1_puzzle_hash,
                    uint64(10000032100000000),
                    [node_1_puzzle_hash]
                ],
                [
                    ConditionOpcode.CREATE_COIN,
                    node_2_puzzle_hash,
                    uint64(10000000000000000),
                    [node_2_puzzle_hash]
                ]
            ]
        )
    )

    # Puzzle reveal for root hash is correct
    assert root_puzzle.get_tree_hash().hex() == root_hash.hex()

    r = root_puzzle.run(0)

    expected_result = Program.to([
        [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
        [
            ConditionOpcode.CREATE_COIN,
            node_1_puzzle_hash,
            uint64(10000032100000000),
            [node_1_puzzle_hash]
        ],
        [
            ConditionOpcode.CREATE_COIN,
            node_2_puzzle_hash,
            uint64(10000000000000000),
            [node_2_puzzle_hash]
        ]
    ])

    # Result of running root is correct
    assert r.get_tree_hash().hex() == expected_result.get_tree_hash().hex()

    node_1_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
                [
                    ConditionOpcode.CREATE_COIN,
                    target_1_puzzle_hash,
                    target_1_amount,
                    [target_1_puzzle_hash]
                ],
                [
                    ConditionOpcode.CREATE_COIN,
                    target_2_puzzle_hash,
                    target_2_amount,
                    [target_2_puzzle_hash]
                ]
            ]
        )
    )

    # Puzzle reveal for node 1 is correct
    assert node_1_puzzle.get_tree_hash().hex() == node_1_puzzle_hash.hex()

    r = node_1_puzzle.run(0)

    expected_result = Program.to([
        [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
        [
            ConditionOpcode.CREATE_COIN,
            target_1_puzzle_hash,
            target_1_amount,
            [target_1_puzzle_hash]
        ],
        [
            ConditionOpcode.CREATE_COIN,
            target_2_puzzle_hash,
            target_2_amount,
            [target_2_puzzle_hash]
        ]
    ])

    # Result of running node 1 is correct
    assert r.get_tree_hash().hex() == expected_result.get_tree_hash().hex()

    node_2_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
                [
                    ConditionOpcode.CREATE_COIN,
                    target_3_puzzle_hash,
                    target_3_amount,
                    [target_3_puzzle_hash]
                ]
            ]
        )
    )

    # Puzzle reveal for node 2 is correct
    assert node_2_puzzle.get_tree_hash().hex() == node_2_puzzle_hash.hex()

    r = node_2_puzzle.run(0)

    expected_result = Program.to([
        [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
        [
            ConditionOpcode.CREATE_COIN,
            target_3_puzzle_hash,
            target_3_amount,
            [target_3_puzzle_hash]
        ]
    ])

    # Result of running node 2 is correct
    assert r.get_tree_hash().hex() == expected_result.get_tree_hash().hex()

    # Parent puzzle lookup (used for puzzle reveals)

    puzzle_create_target_1 = parent_puzzle_lookup.get(target_1_puzzle_hash.hex())
    puzzle_create_target_2 = parent_puzzle_lookup.get(target_2_puzzle_hash.hex())
    puzzle_create_target_3 = parent_puzzle_lookup.get(target_3_puzzle_hash.hex())

    # Targets 1 & 2 are created by spending node 1
    assert puzzle_create_target_1.puzzle.get_tree_hash().hex() == node_1_puzzle_hash.hex()
    assert puzzle_create_target_2.puzzle.get_tree_hash().hex() == node_1_puzzle_hash.hex()

    # Target 3 is created by spending node 2
    assert puzzle_create_target_3.puzzle.get_tree_hash().hex() == node_2_puzzle_hash.hex()

    puzzle_create_node_1 = parent_puzzle_lookup.get(node_1_puzzle_hash.hex())
    puzzle_create_node_2 = parent_puzzle_lookup.get(node_2_puzzle_hash.hex())

    # Nodes 1 & 2 are created by spending root
    assert puzzle_create_node_1.puzzle.get_tree_hash().hex() == root_hash.hex()
    assert puzzle_create_node_2.puzzle.get_tree_hash().hex() == root_hash.hex()


def test_secure_bag_of_cats():
    asset_id = bytes32.fromhex("6d95dae356e32a71db5ddcb42224754a02524c615c5fc35f568c2af04774e589")
    target_1_inner_puzzle_hash = bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    target_1_outer_puzzle_hash = construct_cat_puzzle(CAT_MOD, asset_id, target_1_inner_puzzle_hash).get_tree_hash_precalc(target_1_inner_puzzle_hash)
    target_1_amount = uint64(10000000000000000)
    target_2_inner_puzzle_hash = bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    target_2_outer_puzzle_hash = construct_cat_puzzle(CAT_MOD, asset_id, target_2_inner_puzzle_hash).get_tree_hash_precalc(target_2_inner_puzzle_hash)
    target_2_amount = uint64(32100000000)
    target_3_inner_puzzle_hash = bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4")
    target_3_outer_puzzle_hash = construct_cat_puzzle(CAT_MOD, asset_id, target_3_inner_puzzle_hash).get_tree_hash_precalc(target_3_inner_puzzle_hash)
    target_3_amount = uint64(10000000000000000)

    targets = [
        Target(
            target_1_inner_puzzle_hash,
            target_1_amount
        ),
        Target(
            target_2_inner_puzzle_hash,
            target_2_amount
        ),
        Target(
            target_3_inner_puzzle_hash,
            target_3_amount
        )
    ]
    root_hash, parent_puzzle_lookup = secure_the_bag(targets, 2, asset_id)

    # Calculates correct root hash
    assert root_hash.hex() == "2a21783e7b1f5ab453e45315a35c1e02c4dd7234f3f41d2d64541819431d049d"

    node_1_inner_puzzle_hash = bytes32.fromhex("f2cff3b95ddbaa61a214220d67a20901c584ff16df12ec769844f391d513835c")
    node_1_outer_puzzle_hash = construct_cat_puzzle(CAT_MOD, asset_id, node_1_inner_puzzle_hash).get_tree_hash_precalc(node_1_inner_puzzle_hash)
    node_2_inner_puzzle_hash = bytes32.fromhex("f45579725598a28c5572d8c534be3edf095830de0f984f0eb3d9bb251c71134b")
    node_2_outer_puzzle_hash = construct_cat_puzzle(CAT_MOD, asset_id, node_2_inner_puzzle_hash).get_tree_hash_precalc(node_2_inner_puzzle_hash)

    root_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
                [
                    ConditionOpcode.CREATE_COIN,
                    node_1_inner_puzzle_hash,
                    uint64(10000032100000000),
                    [node_1_inner_puzzle_hash]
                ],
                [
                    ConditionOpcode.CREATE_COIN,
                    node_2_inner_puzzle_hash,
                    uint64(10000000000000000),
                    [node_2_inner_puzzle_hash]
                ]
            ]
        )
    )

    # Puzzle reveal for root hash is correct
    assert root_puzzle.get_tree_hash().hex() == root_hash.hex()

    node_1_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
                [
                    ConditionOpcode.CREATE_COIN,
                    target_1_inner_puzzle_hash,
                    target_1_amount,
                    [target_1_inner_puzzle_hash]
                ],
                [
                    ConditionOpcode.CREATE_COIN,
                    target_2_inner_puzzle_hash,
                    target_2_amount,
                    [target_2_inner_puzzle_hash]
                ]
            ]
        )
    )

    # Puzzle reveal for node 1 is correct
    assert node_1_puzzle.get_tree_hash().hex() == node_1_inner_puzzle_hash.hex()

    node_2_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
                [
                    ConditionOpcode.CREATE_COIN,
                    target_3_inner_puzzle_hash,
                    target_3_amount,
                    [target_3_inner_puzzle_hash]
                ]
            ]
        )
    )

    # Puzzle reveal for node 2 is correct
    assert node_2_puzzle.get_tree_hash().hex() == node_2_inner_puzzle_hash.hex()

    # Parent puzzle lookup (used for puzzle reveals)
    puzzle_create_target_1 = parent_puzzle_lookup.get(target_1_outer_puzzle_hash.hex())
    puzzle_create_target_2 = parent_puzzle_lookup.get(target_2_outer_puzzle_hash.hex())
    puzzle_create_target_3 = parent_puzzle_lookup.get(target_3_outer_puzzle_hash.hex())

    # Targets 1 & 2 are created by spending node 1
    assert puzzle_create_target_1.puzzle.get_tree_hash().hex() == node_1_outer_puzzle_hash.hex()
    assert puzzle_create_target_2.puzzle.get_tree_hash().hex() == node_1_outer_puzzle_hash.hex()

    # Target 3 is created by spending node 2
    assert puzzle_create_target_3.puzzle.get_tree_hash().hex() == node_2_outer_puzzle_hash.hex()

    puzzle_create_node_1 = parent_puzzle_lookup.get(node_1_outer_puzzle_hash.hex())
    puzzle_create_node_2 = parent_puzzle_lookup.get(node_2_outer_puzzle_hash.hex())

    # Nodes 1 & 2 are created by spending root
    assert puzzle_create_node_1.puzzle.get_tree_hash().hex() == construct_cat_puzzle(CAT_MOD, asset_id, root_puzzle).get_tree_hash().hex()
    assert puzzle_create_node_2.puzzle.get_tree_hash().hex() == construct_cat_puzzle(CAT_MOD, asset_id, root_puzzle).get_tree_hash().hex()

def test_parent_of_puzzle_hash():
    target_1_puzzle_hash = bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    target_1_amount = uint64(10000000000000000)
    target_2_puzzle_hash = bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    target_2_amount = uint64(32100000000)
    target_3_puzzle_hash = bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4")
    target_3_amount = uint64(10000000000000000)

    targets = [
        Target(
            target_1_puzzle_hash,
            target_1_amount
        ),
        Target(
            target_2_puzzle_hash,
            target_2_amount
        ),
        Target(
            target_3_puzzle_hash,
            target_3_amount
        )
    ]
    _, parent_puzzle_lookup = secure_the_bag(targets, 2)

    genesis_coin_name = bytes32.fromhex("2676b64fab1f562cc4788cb2a9dbbe31da09da9cc23118dfccf6ad741d652328")
    expected_node_1_coin_name = bytes32.fromhex("32d17491d882934307218e5581b1de2d4eb27905c654afed0f0c3f8b44aa84eb")
    expected_root_coin_name = bytes32.fromhex("f3153d27c1d14581971203f10082fa2db2fbc0fd786a9b210e43f227eca499b5")

    coin_spend, coin_name = parent_of_puzzle_hash(genesis_coin_name, target_1_puzzle_hash, None, parent_puzzle_lookup)

    # Coin name of node 1
    assert coin_spend.coin.name() == expected_node_1_coin_name
    assert coin_name == expected_node_1_coin_name

    node_1_puzzle_hash = parent_puzzle_lookup.get(target_1_puzzle_hash.hex()).puzzle_hash

    coin_spend, coin_name = parent_of_puzzle_hash(genesis_coin_name, node_1_puzzle_hash, None, parent_puzzle_lookup)

    # Coin name of root
    assert coin_spend.coin.name() == expected_root_coin_name
    assert coin_name == expected_root_coin_name

    root_puzzle_hash = parent_puzzle_lookup.get(node_1_puzzle_hash.hex()).puzzle_hash

    coin_spend, puzzle_hash = parent_of_puzzle_hash(genesis_coin_name, root_puzzle_hash, None, parent_puzzle_lookup)

    # Genesis
    assert coin_spend == None
    assert puzzle_hash == bytes32.fromhex("2676b64fab1f562cc4788cb2a9dbbe31da09da9cc23118dfccf6ad741d652328")

    # Confirm expected root coin name is correct
    root_coin_name = std_hash(genesis_coin_name + root_puzzle_hash + int_to_bytes(target_1_amount + target_2_amount + target_3_amount))

    assert root_coin_name == expected_root_coin_name

    node_1_puzzle = Program.to(
        (
            1,
            [
                [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"],
                [
                    ConditionOpcode.CREATE_COIN,
                    target_1_puzzle_hash,
                    target_1_amount,
                    [target_1_puzzle_hash]
                ],
                [
                    ConditionOpcode.CREATE_COIN,
                    target_2_puzzle_hash,
                    target_2_amount,
                    [target_2_puzzle_hash]
                ]
            ]
        )
    )

    # Confirm expected node 1 coin name is correct
    node_1_coin_name = std_hash(root_coin_name + node_1_puzzle.get_tree_hash() + int_to_bytes(target_1_amount + target_2_amount))

    assert node_1_coin_name == expected_node_1_coin_name

def test_read_secure_the_bag_targets():
    targets = read_secure_the_bag_targets("./tests/cats/test.csv", 20000032100000000)

    assert len(targets) == 3

    assert targets[0].puzzle_hash == bytes32.fromhex("4bc6435b409bcbabe53870dae0f03755f6aabb4594c5915ec983acf12a5d1fba")
    assert targets[0].amount == uint64(10000000000000000)

    assert targets[1].puzzle_hash == bytes32.fromhex("f3d5162330c4d6c8b9a0aba5eed999178dd2bf466a7a0289739acc8209122e2c")
    assert targets[1].amount == uint64(32100000000)

    assert targets[2].puzzle_hash == bytes32.fromhex("7ffdeca4f997bde55d249b4a3adb8077782bc4134109698e95b10ea306a138b4")
    assert targets[2].amount == uint64(10000000000000000)

def test_read_secure_the_bag_targets_invalid_net_amount():
    with pytest.raises(Exception):
        read_secure_the_bag_targets("test.csv", 5000000)
