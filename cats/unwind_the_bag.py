import asyncio
import click
import os
from pathlib import Path

from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.config import load_config
from chia.wallet.cat_wallet.cat_utils import construct_cat_puzzle
from chia.wallet.puzzles.cat_loader import CAT_MOD

from secure_the_bag import parent_of_puzzle_hash, read_secure_the_bag_targets, secure_the_bag

from clvm.casts import int_to_bytes
from chia.util.hash import std_hash
@click.command()
@click.pass_context
@click.option(
    "-gcid",
    "--genesis-coin-id",
    required=True,
    help="ID of coin that was spent to create secured bag",
)
@click.option(
    "-th",
    "--tail-hash",
    required=True,
    help="TAIL hash / Asset ID of CAT to unwind from secured bag of CATs",
)
@click.option(
    "-stbtp",
    "--secure-the-bag-targets-path",
    required=True,
    help="Path to CSV file containing targets of secure the bag (inner puzzle hash + amount)",
)
@click.option(
    "-utph",
    "--unwind-target-puzzle-hash",
    required=True,
    help="Puzzle hash of target to unwind from secured bag",
)
def cli(
    ctx: click.Context,
    genesis_coin_id: str,
    tail_hash: str,
    secure_the_bag_targets_path: str,
    unwind_target_puzzle_hash: str
):
    ctx.ensure_object(dict)

    genesis_coin_id = bytes32.fromhex(genesis_coin_id)
    tail_hash_bytes = bytes32.fromhex(tail_hash)
    unwind_target_puzzle_hash = bytes32.fromhex(unwind_target_puzzle_hash)

    chia_root: Path = Path(os.path.expanduser(os.getenv("CHIA_ROOT", "~/.chia/mainnet"))).resolve()

    client = asyncio.get_event_loop().run_until_complete(
        FullNodeRpcClient.create("localhost", 8555, chia_root, load_config(chia_root, "config.yaml"))
    )

    targets = read_secure_the_bag_targets(secure_the_bag_targets_path, None)
    root_puzzle_hash, parent_puzzle_lookup = secure_the_bag(targets, 100, tail_hash_bytes)

    required_coin_spends = []

    current_puzzle_hash = construct_cat_puzzle(CAT_MOD, tail_hash_bytes, unwind_target_puzzle_hash).get_tree_hash(unwind_target_puzzle_hash)

    while True:
        if current_puzzle_hash is None:
            break

        parent_coin_name, parent_puzzle_hash = parent_of_puzzle_hash(genesis_coin_id, current_puzzle_hash, tail_hash_bytes, parent_puzzle_lookup)

        response = asyncio.get_event_loop().run_until_complete(
            client.get_coin_record_by_name(parent_coin_name)
        )

        if response is None:
            # Coin doesn't exist yet so we add to list of required spends and check the parent
            required_coin_spends.append(parent_coin_name)
            current_puzzle_hash = parent_puzzle_hash
            continue

        if response.spent_block_index == 0:
            # We have reached the lowest unspent coin
            required_coin_spends.append(parent_coin_name)
        else:
            # This situation is only expected if somebody else unwraps the bag at the same time
            print("WARNING: Lowest coin is spent. Somebody else might have unwrapped the bag.")
            # Trying this..
            required_coin_spends.append(parent_coin_name)

        break

    print("required_coin_spends", required_coin_spends)

def main():
    cli()


if __name__ == "__main__":
    main()
