from typing import List, Tuple

from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.condition_opcodes import ConditionOpcode
from chia.util.ints import uint64


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

    return results
