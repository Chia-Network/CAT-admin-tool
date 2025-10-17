from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from typing import Any

import click
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.coin_spend import make_spend
from chia.types.condition_opcodes import ConditionOpcode
from chia.util.bech32m import encode_puzzle_hash
from chia.util.byte_types import hexstr_to_bytes
from chia.wallet.cat_wallet.cat_utils import CAT_MOD, construct_cat_puzzle
from chia_rs import CoinSpend
from chia_rs.sized_bytes import bytes32
from chia_rs.sized_ints import uint64
from clvm_tools.binutils import assemble
from clvm_tools.clvmc import compile_clvm_text

# Fees spend asserts this. Message not required as inner puzzle contains hardcoded coin spends
# and doesn't accept a solution.
EMPTY_COIN_ANNOUNCEMENT = [ConditionOpcode.CREATE_COIN_ANNOUNCEMENT, b"$"]


# The clvm loaders in this library automatically search for includable files in the directory './include'
def append_include(search_paths: Iterable[str]) -> list[str]:
    if search_paths:
        search_list = list(search_paths)
        search_list.append("./include")
        return search_list
    else:
        return ["./include"]


def parse_program(program: str | Program, include: Iterable[str] = []) -> Program:
    prog: Program
    if isinstance(program, Program):
        return program
    else:
        if "(" in program:  # If it's raw clvm
            prog = Program.to(assemble(program))
        elif "." not in program:  # If it's a byte string
            prog = Program.from_bytes(hexstr_to_bytes(program))
        else:  # If it's a file
            with open(program) as file:
                filestring: str = file.read()
                if "(" in filestring:  # If it's not compiled
                    # TODO: This should probably be more robust
                    if re.compile(r"\(mod\s").search(filestring):  # If it's Chialisp
                        prog = Program.to(
                            compile_clvm_text(filestring, append_include(include))  # type: ignore[no-untyped-call]
                        )
                    else:  # If it's CLVM
                        prog = Program.to(assemble(filestring))
                else:  # If it's serialized CLVM
                    prog = Program.from_bytes(hexstr_to_bytes(filestring))
        return prog


class Target:
    puzzle_hash: bytes32
    amount: uint64

    def __init__(self, puzzle_hash: bytes32, amount: uint64) -> None:
        self.puzzle_hash = puzzle_hash
        self.amount = amount

    def create_coin_condition(self) -> list[Any]:
        return [
            ConditionOpcode.CREATE_COIN,
            self.puzzle_hash,
            self.amount,
            [self.puzzle_hash],
        ]


class TargetCoin:
    target: Target
    puzzle: Program
    puzzle_hash: bytes32
    amount: uint64

    def __init__(self, target: Target, puzzle: Program, amount: uint64) -> None:
        self.target = target
        self.puzzle = puzzle
        self.puzzle_hash = puzzle.get_tree_hash()
        self.amount = amount


def batch_the_bag(targets: list[Target], leaf_width: int) -> list[list[Target]]:
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


def secure_the_bag(
    targets: list[Target],
    leaf_width: int,
    asset_id: bytes32 | None = None,
    parent_puzzle_lookup: dict[str, TargetCoin] = {},
) -> tuple[bytes32, dict[str, TargetCoin]]:
    """
    Calculates secure the bag root puzzle hash and provides parent puzzle reveal lookup table for spending.

    Secures bag of CATs if optional asset id is passed.
    """

    if len(targets) == 1:
        return targets[0].puzzle_hash, parent_puzzle_lookup

    results: list[Target] = []

    batched_targets = batch_the_bag(targets, leaf_width)
    batch_count = len(batched_targets)

    print(f"Batched the bag into {batch_count} batches")

    processed = 0

    for batch_targets in batched_targets:
        print(f"{round((processed / batch_count) * 100, 2)}% of the way through batches")

        list_of_conditions = [EMPTY_COIN_ANNOUNCEMENT]
        total_amount = 0

        print(f"Creating coin with {len(batch_targets)} targets")

        for target in batch_targets:
            list_of_conditions.append(target.create_coin_condition())
            total_amount += target.amount

        puzzle = Program.to((1, list_of_conditions))
        puzzle_hash = puzzle.get_tree_hash()
        amount = total_amount

        results.append(Target(puzzle_hash, uint64(amount)))

        if asset_id is not None:
            outer_puzzle = construct_cat_puzzle(CAT_MOD, asset_id, puzzle)

        for target in batch_targets:
            if asset_id is not None:
                target_outer_puzzle_hash = construct_cat_puzzle(
                    CAT_MOD, asset_id, Program.to(target.puzzle_hash)
                ).get_tree_hash_precalc(target.puzzle_hash)
                parent_puzzle_lookup[target_outer_puzzle_hash.hex()] = TargetCoin(target, outer_puzzle, uint64(amount))
            else:
                parent_puzzle_lookup[target.puzzle_hash.hex()] = TargetCoin(target, puzzle, uint64(amount))

        processed += 1

    return secure_the_bag(results, leaf_width, asset_id, parent_puzzle_lookup)


def parent_of_puzzle_hash(
    genesis_coin_name: bytes32,
    puzzle_hash: bytes32,
    parent_puzzle_lookup: dict[str, TargetCoin],
) -> tuple[CoinSpend | None, bytes32]:
    parent: TargetCoin | None = parent_puzzle_lookup.get(puzzle_hash.hex())

    if parent is None:
        return None, genesis_coin_name

    # We need the parent of the parent in order to calculate the coin name
    _, parent_coin_info = parent_of_puzzle_hash(genesis_coin_name, parent.puzzle_hash, parent_puzzle_lookup)

    coin = Coin(parent_coin_info, parent.puzzle_hash, parent.amount)

    return make_spend(coin, parent.puzzle, Program.to([])), coin.name()


def read_secure_the_bag_targets(secure_the_bag_targets_path: str, target_amount: int | None) -> list[Target]:
    """
    Reads secure the bag targets file. Validates the net amount sent to targets is equal to the target amount.
    """
    targets: list[Target] = []

    with open(secure_the_bag_targets_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        for [ph, amount] in list(reader):
            targets.append(Target(bytes32.fromhex(ph), uint64(amount)))

    net_amount = sum([target.amount for target in targets])

    if target_amount:
        if net_amount != target_amount:
            raise Exception(f"Net amount of targets not expected amount. Expected {target_amount} but got {net_amount}")

    return targets


@click.command()
@click.pass_context
@click.option(
    "-l",
    "--tail",
    required=True,
    help="The TAIL program to launch this CAT with",
)
@click.option(
    "-c",
    "--curry",
    multiple=True,
    help="An argument to curry into the TAIL",
)
@click.option(
    "-a",
    "--amount",
    required=True,
    type=int,
    help="The amount to issue in mojos (regular XCH will be used to fund this)",
)
@click.option(
    "-stbtp",
    "--secure-the-bag-targets-path",
    help="Path to CSV file containing targets of secure the bag (inner puzzle hash + amount)",
)
@click.option(
    "-lw",
    "--leaf-width",
    required=True,
    default=100,
    show_default=True,
    help="Secure the bag leaf width",
)
@click.option(
    "-pr",
    "--prefix",
    required=True,
    default="xch",
    show_default=True,
    help="Address prefix",
)
def cli(
    ctx: click.Context,
    tail: str,
    curry: tuple[str],
    amount: int,
    secure_the_bag_targets_path: str,
    leaf_width: int,
    prefix: str,
) -> None:
    ctx.ensure_object(dict)

    parsed_tail: Program = parse_program(tail)
    curried_args = [assemble(arg) for arg in curry]

    # Construct the TAIL
    if len(curried_args) > 0:
        curried_tail = parsed_tail.curry(*curried_args)
    else:
        curried_tail = parsed_tail

    targets = read_secure_the_bag_targets(secure_the_bag_targets_path, amount)
    root_puzzle_hash, _ = secure_the_bag(targets, leaf_width, None)
    outer_root_puzzle_hash = construct_cat_puzzle(
        CAT_MOD, curried_tail.get_tree_hash(), Program.to(root_puzzle_hash)
    ).get_tree_hash_precalc(root_puzzle_hash)

    print(f"Secure the bag root puzzle hash: {outer_root_puzzle_hash}")

    address = encode_puzzle_hash(root_puzzle_hash, prefix)

    print(f"Secure the bag root address: {address}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
