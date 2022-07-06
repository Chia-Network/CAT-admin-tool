from typing import Dict, List, Tuple, Union

from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.condition_opcodes import ConditionOpcode
from chia.util.hash import std_hash
from chia.util.ints import uint64
from chia.wallet.cat_wallet.cat_utils import construct_cat_puzzle
from chia.wallet.puzzles.cat_loader import CAT_MOD
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


def batch_the_bag(targets: List[Target], leaf_width: int) -> List[List[Target]]:
    """
    Batches the bag by leaf width.
    """
    results = []
    current_batch = []

    for index, target in enumerate(targets):
        current_batch.append(target)
        
        if len(current_batch) == leaf_width or index == len(targets) - 1:
            results.append(current_batch)
            current_batch = []

    return results


def secure_the_bag(targets: List[Target], leaf_width: int, asset_id: Union[bytes32, None] = None, parent_puzzle_lookup: Dict = {}) -> Tuple[bytes32, Dict[str, Program]]:
    """
    Calculates secure the bag root puzzle hash and provides parent puzzle reveal lookup table for spending.

    Secures bag of CATs if optional asset id is passed.
    """

    if len(targets) == 1:
        if asset_id is not None:
            return construct_cat_puzzle(CAT_MOD, asset_id, targets[0].puzzle_hash).get_tree_hash(targets[0].puzzle_hash), parent_puzzle_lookup

        return targets[0].puzzle_hash, parent_puzzle_lookup

    results: List[Target] = []

    batched_targets = batch_the_bag(targets, leaf_width)

    for batch_targets in batched_targets:

        list_of_conditions = [EMPTY_COIN_ANNOUNCEMENT]
        total_amount = 0

        for target in batch_targets:
            list_of_conditions.append(target.create_coin_condition())
            total_amount += target.amount

        puzzle = Program.to((1, list_of_conditions))
        puzzle_hash = puzzle.get_tree_hash()
        amount = total_amount

        results.append(Target(puzzle_hash, amount))

        if asset_id is not None:
            outer_puzzle = construct_cat_puzzle(CAT_MOD, asset_id, puzzle)

        for target in batch_targets:
            if asset_id is not None:
                target_outer_puzzle_hash = construct_cat_puzzle(CAT_MOD, asset_id, target.puzzle_hash).get_tree_hash(target.puzzle_hash)
                parent_puzzle_lookup[target_outer_puzzle_hash.hex()] = outer_puzzle
            else:
                parent_puzzle_lookup[target.puzzle_hash.hex()] = puzzle

    return secure_the_bag(results, leaf_width, asset_id, parent_puzzle_lookup)