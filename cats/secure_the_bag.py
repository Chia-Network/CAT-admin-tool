from typing import Dict, List, Tuple

from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.condition_opcodes import ConditionOpcode
from chia.util.hash import std_hash
from chia.util.ints import uint64
from clvm.casts import int_to_bytes

# Fees spend asserts this. Message not required as inner puzzle contains hardcoded coin spends and doesn't accept a solution.
EMPTY_COIN_ANNOUNCEMENT = [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, None]


class Target:
    puzzle_hash: bytes32
    amount: uint64

    def __init__(self, puzzle_hash: bytes32, amount: uint64) -> None:
        self.puzzle_hash = puzzle_hash
        self.amount = amount
    
    def create_coin_condition(self) -> Tuple[bytes, bytes32, uint64, Tuple[bytes32]]:
        return [ConditionOpcode.CREATE_COIN, self.puzzle_hash, self.amount, [self.puzzle_hash]]


def batch_the_bag(targets: List[Target], leaf_width: int) -> List[Target]:
    """
    Batches the bag making sure not to include multiple coins with the same
    puzzle hash and amount in a batch
    """
    results = []
    batch_cache = {}
    current_batch = []
    collisions = []

    for index, target in enumerate(targets):
        remaining_collisions = []
        for collision in collisions:
            key = std_hash(collision.puzzle_hash + int_to_bytes(collision.amount))

            if batch_cache.get(key):
                remaining_collisions.append(collision)
            else:
                current_batch.append(collision)
                batch_cache[key] = True
            
            if len(current_batch) == leaf_width:
                results.append(current_batch)
                batch_cache = {}
                current_batch = []
        
        collisions = remaining_collisions

        key = std_hash(target.puzzle_hash + int_to_bytes(target.amount))

        if batch_cache.get(key):
            collisions.append(target)
        else:
            current_batch.append(target)
            batch_cache[key] = True
        
        if len(current_batch) == leaf_width or index == len(targets) - 1:
            results.append(current_batch)
            batch_cache = {}
            current_batch = []

    return results


def secure_the_bag(targets: List[Target], leaf_width: int, parent_puzzle_lookup: Dict[str, Program] = {}) -> Tuple[bytes32, Dict[str, Program]]:
    """
    Calculates secure the bag root puzzle hash
    """

    if len(targets) == 1:
        return targets[0].puzzle_hash, parent_puzzle_lookup

    results: List[Target] = []

    batched_targets = batch_the_bag(targets, leaf_width)

    for batch_targets in batched_targets:

        list_of_conditions = [EMPTY_COIN_ANNOUNCEMENT]
        total_amount = 0

        for target in batch_targets:
            list_of_conditions.append(target.create_coin_condition())
            total_amount += target.amount

        inner_puzzle = Program.to((1, list_of_conditions))
        inner_puzzle_hash = inner_puzzle.get_tree_hash()
        amount = total_amount

        results.append(Target(inner_puzzle_hash, amount))

        for target in batch_targets:
            parent_puzzle_lookup[target.puzzle_hash.hex()] = inner_puzzle

    return secure_the_bag(results, leaf_width, parent_puzzle_lookup)
