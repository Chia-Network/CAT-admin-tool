import asyncio
import concurrent.futures
import pytest

from click.testing import CliRunner, Result
from chia.simulator.setup_nodes import SimulatorsAndWalletsServices
from chia.types.peer_info import PeerInfo
from chia.util.bech32m import encode_puzzle_hash
from chia.util.ints import uint16

from cats.cats import cli

@pytest.mark.asyncio
async def test_cat_mint(one_wallet_and_one_simulator_services: SimulatorsAndWalletsServices):
    # Wallet environment setup
    num_blocks = 1
    full_nodes, wallets, bt = one_wallet_and_one_simulator_services
    full_node_api = full_nodes[0]._api
    full_node_server = full_node_api.full_node.server
    wallet_service_0 = wallets[0]
    wallet_node_0 = wallet_service_0._node
    wallet_0 = wallet_node_0.wallet_state_manager.main_wallet
    assert wallet_service_0.rpc_server is not None

    wallet_node_0.config["automatically_add_unknown_cats"] = True
    wallet_node_0.config["trusted_peers"] = {
        full_node_api.full_node.server.node_id.hex(): full_node_api.full_node.server.node_id.hex()
    }

    await wallet_node_0.server.start_client(PeerInfo("127.0.0.1", uint16(full_node_server._port)), None)
    await full_node_api.farm_blocks_to_wallet(count=num_blocks, wallet=wallet_0)
    await full_node_api.wait_for_wallet_synced(wallet_node=wallet_node_0, timeout=20)

    self_address, fingerprint, root_path = encode_puzzle_hash(await wallet_0.get_new_puzzlehash(), "xch"), str(wallet_0.wallet_state_manager.private_key.get_g1().get_fingerprint()), str(wallet_service_0.root_path)

    # Test help as a sanity check
    runner = CliRunner()
    result: Result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0

    # Issuance parameters
    tail_as_hex = "80"
    arg_to_curry = "80"
    expected_tail = "ff02ffff0180ffff04ff80ff018080"  # opc "(a (q . ()) (c () 1))"
    solution = "9a7461696c20736f6c7574696f6e20666f72206361742074657374"  # opc "'tail solution for cat test'"
    amount = "13"
    fee = "100"  # mojos

    result = runner.invoke(cli, [
        "--tail",
        tail_as_hex,
        "--curry",
        arg_to_curry,
        "--solution",
        solution,
        "--send-to",
        self_address,
        "--amount",
        amount,
        "--fee",
        fee,
        "--fingerprint",
        fingerprint,
        "--select-coin",
        "--root-path",
        root_path,
    ])
    assert result.exit_code == 0

    result = runner.invoke(cli, [
        "--tail",
        tail_as_hex,
        "--curry",
        arg_to_curry,
        "--solution",
        solution,
        "--send-to",
        self_address,
        "--amount",
        amount,
        "--fee",
        fee,
        "--fingerprint",
        fingerprint,
        "--root-path",
        root_path,
        "--as-bytes",
    ])
    assert result.exit_code == 0
    assert expected_tail in result.output
    assert solution in result.output

    result = runner.invoke(cli, [
        "--tail",
        tail_as_hex,
        "--curry",
        arg_to_curry,
        "--solution",
        solution,
        "--send-to",
        self_address,
        "--amount",
        amount,
        "--fee",
        fee,
        "--fingerprint",
        fingerprint,
        "--root-path",
        root_path,
    ], input="Y\n")
    assert result.exit_code == 0

    await full_node_api.farm_blocks_to_wallet(count=num_blocks, wallet=wallet_0)
    await full_node_api.wait_for_wallet_synced(wallet_node=wallet_node_0, timeout=20)
    assert len(wallet_node_0.wallet_state_manager.wallets) == 2
