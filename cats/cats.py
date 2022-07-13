import click
import asyncio
import re
import json

from typing import Tuple, Iterable, Union, List
from blspy import G2Element, AugSchemeMPL

from chia.cmds.wallet_funcs import get_wallet
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.util.byte_types import hexstr_to_bytes
from chia.types.blockchain_format.program import Program
from clvm_tools.clvmc import compile_clvm_text
from clvm_tools.binutils import assemble
from chia.types.spend_bundle import SpendBundle
from chia.wallet.cat_wallet.cat_utils import (
    construct_cat_puzzle,
    CAT_MOD,
    SpendableCAT,
    unsigned_spend_bundle_for_spendable_cats,
)
from chia.util.bech32m import decode_puzzle_hash
from secure_the_bag import read_secure_the_bag_targets, secure_the_bag
from utils import get_client, get_signed_tx


async def push_tx(fingerprint, bundle):
    try:
        wallet_client: WalletRpcClient = await get_client()
        wallet_client_f, _ = await get_wallet(wallet_client, fingerprint)
        return await wallet_client_f.push_tx(bundle)
    finally:
        wallet_client.close()
        await wallet_client.await_closed()


# The clvm loaders in this library automatically search for includable files in the directory './include'
def append_include(search_paths: Iterable[str]) -> List[str]:
    if search_paths:
        search_list = list(search_paths)
        search_list.append("./include")
        return search_list
    else:
        return ["./include"]


def parse_program(program: Union[str, Program], include: Iterable = []) -> Program:
    if isinstance(program, Program):
        return program
    else:
        if "(" in program:  # If it's raw clvm
            prog = Program.to(assemble(program))
        elif "." not in program:  # If it's a byte string
            prog = Program.from_bytes(hexstr_to_bytes(program))
        else:  # If it's a file
            with open(program, "r") as file:
                filestring: str = file.read()
                if "(" in filestring:  # If it's not compiled
                    # TODO: This should probably be more robust
                    if re.compile(r"\(mod\s").search(filestring):  # If it's Chialisp
                        prog = Program.to(
                            compile_clvm_text(filestring, append_include(include))
                        )
                    else:  # If it's CLVM
                        prog = Program.to(assemble(filestring))
                else:  # If it's serialized CLVM
                    prog = Program.from_bytes(hexstr_to_bytes(filestring))
        return prog


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


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
    "-s",
    "--solution",
    required=True,
    default="()",
    show_default=True,
    help="The solution to the TAIL program",
)
@click.option(
    "-t",
    "--send-to",
    required=True,
    help="The address these CATs will appear at once they are issued",
)
@click.option(
    "-a",
    "--amount",
    required=True,
    type=int,
    help="The amount to issue in mojos (regular XCH will be used to fund this)",
)
@click.option(
    "-m",
    "--fee",
    required=True,
    default=0,
    show_default=True,
    help="The fees for the transaction, in mojos",
)
@click.option(
    "-f",
    "--fingerprint",
    type=int,
    help="The wallet fingerprint to use as funds",
)
@click.option(
    "-sig",
    "--signature",
    multiple=True,
    help="A signature to aggregate with the transaction",
)
@click.option(
    "-as",
    "--spend",
    multiple=True,
    help="An additional spend to aggregate with the transaction",
)
@click.option(
    "-b",
    "--as-bytes",
    is_flag=True,
    help="Output the spend bundle as a sequence of bytes instead of JSON",
)
@click.option(
    "-sc",
    "--select-coin",
    is_flag=True,
    help="Stop the process once a coin from the wallet has been selected and return the coin",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Quiet mode will not ask to push transaction to the network",
)
@click.option(
    "-p",
    "--push",
    is_flag=True,
    help="Automatically push transaction to the network in quiet mode",
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
def cli(
    ctx: click.Context,
    tail: str,
    curry: Tuple[str],
    solution: str,
    send_to: str,
    amount: int,
    fee: int,
    fingerprint: int,
    signature: Tuple[str],
    spend: Tuple[str],
    as_bytes: bool,
    select_coin: bool,
    quiet: bool,
    push: bool,
    secure_the_bag_targets_path: str,
    leaf_width: int
):
    ctx.ensure_object(dict)

    tail = parse_program(tail)
    curried_args = [assemble(arg) for arg in curry]
    solution = parse_program(solution)

    aggregated_signature = G2Element()
    for sig in signature:
        aggregated_signature = AugSchemeMPL.aggregate(
            [aggregated_signature, G2Element.from_bytes(hexstr_to_bytes(sig))]
        )

    aggregated_spend = SpendBundle([], G2Element())
    for bundle in spend:
        aggregated_spend = SpendBundle.aggregate(
            [aggregated_spend, SpendBundle.from_bytes(hexstr_to_bytes(bundle))]
        )

    # Construct the TAIL
    if len(curried_args) > 0:
        curried_tail = tail.curry(*curried_args)
    else:
        curried_tail = tail
    
    if secure_the_bag_targets_path:
        targets = read_secure_the_bag_targets(secure_the_bag_targets_path, amount)
        root_puzzle_hash, _ = secure_the_bag(targets, leaf_width, None)
        outer_root_puzzle_hash = construct_cat_puzzle(CAT_MOD, curried_tail.get_tree_hash(), root_puzzle_hash).get_tree_hash(root_puzzle_hash)
        print(f"Secure the bag root puzzle hash: {outer_root_puzzle_hash}")
        address = root_puzzle_hash
    else:
        address = decode_puzzle_hash(send_to)

    # Construct the intermediate puzzle
    p2_puzzle = Program.to(
        (1, [[51, 0, -113, curried_tail, solution], [51, address, amount, [address]]])
    )

    # Wrap the intermediate puzzle in a CAT wrapper
    cat_puzzle = construct_cat_puzzle(CAT_MOD, curried_tail.get_tree_hash(), p2_puzzle)
    cat_ph = cat_puzzle.get_tree_hash()

    # Get a signed transaction from the wallet
    signed_tx = asyncio.get_event_loop().run_until_complete(
        get_signed_tx(fingerprint, cat_ph, amount, fee)
    )
    eve_coin = list(
        filter(lambda c: c.puzzle_hash == cat_ph, signed_tx.spend_bundle.additions())
    )[0]

    primary_coin = list(
        filter(
            lambda c: c.name() == eve_coin.parent_coin_info,
            signed_tx.spend_bundle.removals(),
        )
    )[0]

    # This is where we exit if we're only looking for the selected coin
    if select_coin:
        
        print(json.dumps(primary_coin.to_json_dict(), sort_keys=True, indent=4))
        print(f"Name: {primary_coin.name().hex()}")
        return

    # Create the CAT spend
    spendable_eve = SpendableCAT(
        eve_coin,
        curried_tail.get_tree_hash(),
        p2_puzzle,
        Program.to([]),
        limitations_solution=solution,
        limitations_program_reveal=curried_tail,
    )
    eve_spend = unsigned_spend_bundle_for_spendable_cats(CAT_MOD, [spendable_eve])

    print(f"Secure the bag genesis coin ID: {eve_coin.name()}")

    # Aggregate everything together
    final_bundle = SpendBundle.aggregate(
        [
            signed_tx.spend_bundle,
            eve_spend,
            aggregated_spend,
            SpendBundle([], aggregated_signature),
        ]
    )

    if as_bytes:
        final_bundle_dump = bytes(final_bundle).hex()
    else:
        final_bundle_dump = json.dumps(final_bundle.to_json_dict(), sort_keys=True, indent=4)

    confirmation = push

    if not quiet:
        confirmation = input(
            "The transaction has been created, would you like to push it to the network? (Y/N)"
        ) in ["y", "Y", "yes", "Yes"]
    if confirmation:
        response = asyncio.get_event_loop().run_until_complete(
            push_tx(fingerprint, final_bundle)
        )
        if "error" in response:
            print(f"Error pushing transaction: {response['error']}")
            return
        print(f"Successfully pushed the transaction to the network")

    print(f"Asset ID / TAIL Hash: {curried_tail.get_tree_hash().hex()}")
    if not confirmation:
        print(f"Spend Bundle: {final_bundle_dump}")


def main():
    cli()


if __name__ == "__main__":
    main()
