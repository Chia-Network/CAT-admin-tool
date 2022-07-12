import asyncio
from collections import defaultdict
from blspy import G2Element
import click
import os
import time
from typing import Coroutine, Dict, List
from pathlib import Path

from chia.cmds.wallet_funcs import get_wallet
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_record import CoinRecord
from chia.types.spend_bundle import CoinSpend, SpendBundle
from chia.util.config import load_config
from chia.wallet.cat_wallet.cat_utils import (
    construct_cat_puzzle,
    CAT_MOD,
    SpendableCAT,
    match_cat_puzzle,
    unsigned_spend_bundle_for_spendable_cats,
)
from chia.wallet.lineage_proof import LineageProof
from chia.wallet.puzzles.cat_loader import CAT_MOD

from secure_the_bag import batch_the_bag, parent_of_puzzle_hash, read_secure_the_bag_targets, secure_the_bag, TargetCoin

NULL_SIGNATURE = G2Element()


async def unspent_coin_exists(full_node_client: FullNodeRpcClient, coin_name: bytes32):
    """
    Checks if an unspent coin exists.

    Raises an exception if coin has already been spent.
    """
    coin_record = await full_node_client.get_coin_record_by_name(coin_name)

    if coin_record is None:
        return False

    if coin_record.spent_block_index > 0:
        raise Exception("Coin {} has already been spent".format(coin_name))

    return True


async def wait_for_unspent_coin(full_node_client: FullNodeRpcClient, coin_name: bytes32):
    """
    Repeatedly poll full node until unspent coin is created.

    Raises an exception if coin has already been spent.
    """
    while True:
        print(f"Waiting for unspent coin {coin_name}")

        exists = await unspent_coin_exists(full_node_client, coin_name)

        if exists:
            print(f"Coin {coin_name} exists and is unspent")

            break

        print(f"Unspent coin {coin_name} does not exist")

        await asyncio.sleep(3)


async def wait_for_coin_spend(full_node_client: FullNodeRpcClient, coin_name: bytes32):
    """
    Repeatedly poll full node until coin is spent.

    This is used to wait for coins spend before spending children.
    """
    while True:
        print(f"Waiting for coin spend {coin_name}")

        coin_record = await full_node_client.get_coin_record_by_name(coin_name)

        if coin_record is None:
            print(f"Coin {coin_name} does not exist")

            continue

        if coin_record.spent_block_index > 0:
            print(f"Coin {coin_name} has been spent")

            break

        print(f"Coin {coin_name} has not been spent")

        await asyncio.sleep(3)


async def get_unwind(full_node_client: FullNodeRpcClient, genesis_coin_id: bytes32, tail_hash_bytes: bytes32, parent_puzzle_lookup: Dict[str, TargetCoin], target_puzzle_hash: bytes32) -> List[CoinSpend]:
    required_coin_spends: List[CoinSpend] = []

    current_puzzle_hash = target_puzzle_hash

    while True:
        if current_puzzle_hash is None:
            break

        coin_spend, _ = parent_of_puzzle_hash(genesis_coin_id, current_puzzle_hash, tail_hash_bytes, parent_puzzle_lookup)

        if coin_spend is None:
            break

        response = await full_node_client.get_coin_record_by_name(coin_spend.coin.name())

        if response is None:
            # Coin doesn't exist yet so we add to list of required spends and check the parent
            required_coin_spends.append(coin_spend)
            current_puzzle_hash = coin_spend.coin.puzzle_hash
            continue

        if response.spent_block_index == 0:
            # We have reached the lowest unspent coin
            required_coin_spends.append(coin_spend)
        else:
            # This situation is only expected if the bag has already been unwound (possibly by somebody else)
            print("WARNING: Lowest coin is spent. Secured bag already unwound.")

        break
    
    return required_coin_spends


async def unwind_coin_spend(full_node_client: FullNodeRpcClient, tail_hash_bytes: bytes32, coin_spend: CoinSpend) -> SpendBundle:
    # Wait for unspent coin to exist before trying to spend it
    await wait_for_unspent_coin(full_node_client, coin_spend.coin.name())

    matched, curried_args = match_cat_puzzle(coin_spend.puzzle_reveal)

    if matched is None:
        raise Exception("Expected CAT")

    _, _, inner_puzzle = curried_args

    # Get parent coin info as required for lineage proof when spending this CAT coin
    parent_r: CoinRecord = await full_node_client.get_coin_record_by_name(coin_spend.coin.parent_coin_info)
    parent: CoinSpend = await full_node_client.get_puzzle_and_solution(coin_spend.coin.parent_coin_info, parent_r.spent_block_index)

    parent_matched, parent_curried_args = match_cat_puzzle(parent.puzzle_reveal)

    if parent_matched is None:
        raise Exception("Expected parent to be CAT")

    _, _, parent_inner_puzzle = parent_curried_args

    spendable_cat = SpendableCAT(
        coin_spend.coin,
        tail_hash_bytes,
        inner_puzzle,
        Program.to([]),
        lineage_proof=LineageProof(parent_r.coin.parent_coin_info, parent_inner_puzzle.get_tree_hash(), parent.coin.amount)
    )
    cat_spend = unsigned_spend_bundle_for_spendable_cats(CAT_MOD, [spendable_cat])

    # Throw an error before pushing to full node if spend is invalid
    _ = cat_spend.coin_spends[0].puzzle_reveal.run_with_cost(0, cat_spend.coin_spends[0].solution)

    return cat_spend

def combine_spend_bundles_with_fee(batch: List[SpendBundle], unwind_fee: int):
    coin_spends: List[CoinSpend] = []

    for spend_bundle in batch:
        coin_spends += spend_bundle.coin_spends
    
    # if unwind_fee > 0:
    #     # todo: add fee to spend bundle here...
    #     foo = "bar"
    
    return SpendBundle(coin_spends, NULL_SIGNATURE)

async def unwind_the_bag(full_node_client: FullNodeRpcClient, wallet_client: WalletRpcClient, unwind_target_puzzle_hash_bytes: bytes32, tail_hash_bytes: bytes32, genesis_coin_id: bytes32, parent_puzzle_lookup: Dict[str, TargetCoin], unwind_fee: int) -> List[CoinSpend]:
    current_puzzle_hash = construct_cat_puzzle(CAT_MOD, tail_hash_bytes, unwind_target_puzzle_hash_bytes).get_tree_hash(unwind_target_puzzle_hash_bytes)

    print(f"Getting unwind for {current_puzzle_hash}")

    required_coin_spends: List[CoinSpend] = await get_unwind(full_node_client, genesis_coin_id, tail_hash_bytes, parent_puzzle_lookup, current_puzzle_hash)

    print(f"{len(required_coin_spends)} spends required to unwind the bag to {unwind_target_puzzle_hash_bytes}")

    return required_coin_spends[::-1]

        

async def app(chia_config, chia_root, secure_the_bag_targets_path: str, leaf_width: int, tail_hash_bytes: bytes32, unwind_target_puzzle_hash_bytes: bytes32, genesis_coin_id: bytes32, unwind_fee: int):
    full_node_client = await FullNodeRpcClient.create(chia_config["self_hostname"], chia_config["full_node"]["rpc_port"], chia_root, load_config(chia_root, "config.yaml"))
    wallet_client = await WalletRpcClient.create(chia_config["self_hostname"], chia_config["wallet"]["rpc_port"], chia_root, load_config(chia_root, "config.yaml"))

    targets = read_secure_the_bag_targets(secure_the_bag_targets_path, None)
    _, parent_puzzle_lookup = secure_the_bag(targets, leaf_width, tail_hash_bytes)

    if unwind_target_puzzle_hash_bytes is not None:
        # Unwinding to a single target has to be done sequentially as each spend is dependant on the parent being spent
        print(f"Unwinding secured bag to {unwind_target_puzzle_hash_bytes}")

        coin_spends = await unwind_the_bag(full_node_client, wallet_client, unwind_target_puzzle_hash_bytes, tail_hash_bytes, genesis_coin_id, parent_puzzle_lookup, unwind_fee)
        
        for coin_spend in coin_spends[::-1]:
            cat_spend = await unwind_coin_spend(full_node_client, tail_hash_bytes, coin_spend)
            wallet_client_f, _ = await get_wallet(wallet_client, None)
            response = await wallet_client_f.push_tx(cat_spend)

            print("Transaction pushed to full node", response)

            # Wait for parent coin to be spent before attempting to spend children
            await wait_for_coin_spend(full_node_client, coin_spend.coin.name())
    else:
        # Unwinding the entire secured bag can involve batching spends together for speed
        # Care must be taken to only batch together spends where the parent has been spent otherwise one invalid spend could invalidate the entire spend bundle
        print("Unwinding entire secured bag")

        batched_targets = batch_the_bag(targets, leaf_width)

        # Dictionary of spends at each level of the tree so they can be batched based on parents that have already been spent
        level_coin_spends: Dict[int, Dict[str, CoinSpend]] = defaultdict(dict)
        max_depth = 0

        # Unwind to the first target coin in each batch
        for batch_targets in batched_targets:
            unwound_spends = await unwind_the_bag(full_node_client, wallet_client, batch_targets[0].puzzle_hash, tail_hash_bytes, genesis_coin_id, parent_puzzle_lookup, unwind_fee)

            print(f"{len(unwound_spends)} spends to {batch_targets[0].puzzle_hash}")

            for (index, coin_spend) in enumerate(unwound_spends):
                level_coin_spends[index][coin_spend.coin.puzzle_hash.hex()] = coin_spend
                if index > max_depth:
                    max_depth = index
        
        for depth in range(0, max_depth + 1):
            level = level_coin_spends[depth]

            # Larger batch_size e.g. 25 can result in COST_EXCEEDS_MAX
            batch_size = 10
            spent_coin_names: List[bytes32] = []
            bundle_spends: List[CoinSpend] = []

            print(f"About to iterate {len(level.values())} times for depth {depth}") 

            i = 0
            for coin_spend in level.values():
                i += 1
                cat_spend = await unwind_coin_spend(full_node_client, tail_hash_bytes, coin_spend)
                wallet_client_f, _ = await get_wallet(wallet_client, None)

                bundle_spends += cat_spend.coin_spends
                spent_coin_names.append(coin_spend.coin.name())

                print(f"len(bundle_spends) {len(bundle_spends)}")
                print(f"i == len(level.values() {i == len(level.values())}")

                if len(bundle_spends) >= batch_size or i == len(level.values()):
                    await wallet_client_f.push_tx(SpendBundle(bundle_spends, cat_spend.aggregated_signature))

                    print(f"Transaction containing {len(bundle_spends)} coin spends at tree depth {depth} pushed to full node")

                    bundle_spends = []

                    # Wait for this batch to be spent before attempting next spends
                    # Important for spending children of coins we just created
                    coin_spend_waits: List[Coroutine] = []
                    
                    for coin_name in spent_coin_names:
                        coin_spend_waits.append(wait_for_coin_spend(full_node_client, coin_name))
                    
                    await asyncio.gather(*coin_spend_waits)
                    
                    spent_coin_names = []

    full_node_client.close()
    wallet_client.close()


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
    required=False,
    help="Puzzle hash of target to unwind from secured bag",
)
@click.option(
    "-uf",
    "--unwind-fee",
    required=True,
    default=0,
    show_default=True,
    help="Fee paid for each unwind spend. Enough mojos must be available to cover all spends.",
)
def cli(
    ctx: click.Context,
    genesis_coin_id: str,
    tail_hash: str,
    secure_the_bag_targets_path: str,
    unwind_target_puzzle_hash: str,
    unwind_fee: int
):
    ctx.ensure_object(dict)

    leaf_width = 100
    genesis_coin_id = bytes32.fromhex(genesis_coin_id)
    tail_hash_bytes = bytes32.fromhex(tail_hash)
    unwind_target_puzzle_hash_bytes = None
    if unwind_target_puzzle_hash:
        unwind_target_puzzle_hash_bytes = bytes32.fromhex(unwind_target_puzzle_hash)

    chia_root: Path = Path(os.path.expanduser(os.getenv("CHIA_ROOT", "~/.chia/mainnet"))).resolve()
    chia_config = load_config(chia_root, "config.yaml")

    asyncio.get_event_loop().run_until_complete(
        app(chia_config, chia_root, secure_the_bag_targets_path, leaf_width, tail_hash_bytes, unwind_target_puzzle_hash_bytes, genesis_coin_id, unwind_fee)
    )



def main():
    cli()


if __name__ == "__main__":
    main()
