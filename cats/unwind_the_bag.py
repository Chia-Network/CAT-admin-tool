import asyncio
from blspy import G2Element
import click
import os
from typing import List
from pathlib import Path

from chia.cmds.wallet_funcs import get_wallet
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.spend_bundle import CoinSpend, SpendBundle
from chia.util.config import load_config
from chia.wallet.cat_wallet.cat_utils import construct_cat_puzzle
from chia.wallet.puzzles.cat_loader import CAT_MOD

from secure_the_bag import parent_of_puzzle_hash, read_secure_the_bag_targets, secure_the_bag

NULL_SIGNATURE = G2Element()


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
    chia_config = load_config(chia_root, "config.yaml")

    full_node_client = asyncio.get_event_loop().run_until_complete(
        FullNodeRpcClient.create(chia_config["self_hostname"], chia_config["full_node"]["rpc_port"], chia_root, load_config(chia_root, "config.yaml"))
    )
    wallet_client = asyncio.get_event_loop().run_until_complete(
        WalletRpcClient.create(chia_config["self_hostname"], chia_config["wallet"]["rpc_port"], chia_root, load_config(chia_root, "config.yaml"))
    )

    targets = read_secure_the_bag_targets(secure_the_bag_targets_path, None)
    _, parent_puzzle_lookup = secure_the_bag(targets, 100, tail_hash_bytes)

    required_coin_spends: List[CoinSpend] = []

    current_puzzle_hash = construct_cat_puzzle(CAT_MOD, tail_hash_bytes, unwind_target_puzzle_hash).get_tree_hash(unwind_target_puzzle_hash)

    while True:
        if current_puzzle_hash is None:
            break

        coin_spend, _ = parent_of_puzzle_hash(genesis_coin_id, current_puzzle_hash, tail_hash_bytes, parent_puzzle_lookup)

        if coin_spend is None:
            break

        response = asyncio.get_event_loop().run_until_complete(
            full_node_client.get_coin_record_by_name(coin_spend.coin.name())
        )

        if response is None:
            # Coin doesn't exist yet so we add to list of required spends and check the parent
            required_coin_spends.append(coin_spend)
            current_puzzle_hash = coin_spend.coin.puzzle_hash
            continue

        if response.spent_block_index == 0:
            # We have reached the lowest unspent coin
            required_coin_spends.append(coin_spend)
        else:
            # This situation is only expected if somebody else unwraps the bag at the same time
            print("WARNING: Lowest coin is spent. Somebody else might have unwrapped the bag.")

        break

    print(f"{len(required_coin_spends)} spends required to unwind the bag")

    for coin_spend in required_coin_spends[::-1]:
        print(f"Spending coin {coin_spend.coin.name()}")

        # No signature required as anybody can unwind the bag
        spend_bundle = SpendBundle([coin_spend], NULL_SIGNATURE)

        wallet_client_f, _ = asyncio.get_event_loop().run_until_complete(
            get_wallet(wallet_client, None)
        )
        response = asyncio.get_event_loop().run_until_complete(
            wallet_client_f.push_tx(spend_bundle)
        )

        print("fin", response)
        

def main():
    cli()


if __name__ == "__main__":
    main()
