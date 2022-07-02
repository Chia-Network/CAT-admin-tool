from cats.secure_the_bag import batch_the_bag, Target

from chia.types.blockchain_format.sized_bytes import bytes32
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
    root_hash = secure_the_bag(targets, 2)

    assert root_hash.hex() == "bbffed16fdfe5b4c79fced8d04d913a68ea4a028e843e4fb09df18d432713810"
