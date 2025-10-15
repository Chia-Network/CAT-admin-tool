from __future__ import annotations

import contextlib
import io

import pytest
from chia._tests.util.setup_nodes import SimulatorsAndWalletsServices
from chia.types.blockchain_format.coin import Coin
from chia.types.peer_info import PeerInfo
from chia.util.bech32m import encode_puzzle_hash
from chia.wallet.util.tx_config import DEFAULT_TX_CONFIG
from chia_rs.sized_bytes import bytes32
from chia_rs.sized_ints import uint16, uint64

from cats.cats import cmd_func


@pytest.mark.asyncio
async def test_cat_mint(
    one_wallet_and_one_simulator_services: SimulatorsAndWalletsServices,
) -> None:
    # Wallet environment setup
    num_blocks = 1
    full_nodes, wallets, _bt = one_wallet_and_one_simulator_services
    full_node_api = full_nodes[0]._api
    full_node_server = full_node_api.full_node.server
    wallet_service_0 = wallets[0]
    wallet_node_0 = wallet_service_0._node
    wallet_0 = wallet_node_0.wallet_state_manager.main_wallet
    assert wallet_service_0.rpc_server is not None
    assert wallet_service_0.rpc_server.webserver is not None

    wallet_node_0.config["automatically_add_unknown_cats"] = True
    wallet_node_0.config["trusted_peers"] = {
        full_node_api.full_node.server.node_id.hex(): full_node_api.full_node.server.node_id.hex()
    }

    assert full_node_server._port is not None
    await wallet_node_0.server.start_client(PeerInfo("127.0.0.1", uint16(full_node_server._port)), None)
    await full_node_api.farm_blocks_to_wallet(count=num_blocks, wallet=wallet_0)
    await full_node_api.wait_for_wallet_synced(wallet_node=wallet_node_0, timeout=20)

    async with wallet_0.wallet_state_manager.new_action_scope(DEFAULT_TX_CONFIG, push=True) as action_scope:
        ph = await action_scope.get_puzzle_hash(wallet_0.wallet_state_manager)
    self_address = encode_puzzle_hash(ph, "xch")
    fingerprint = wallet_0.wallet_state_manager.get_master_private_key().get_g1().get_fingerprint()
    root_path = str(wallet_service_0.root_path)

    # Issuance parameters
    tail_as_hex = "80"
    args_to_curry = ("80",)
    expected_tail = "ff02ffff0180ffff04ffff0150ff018080"  # opc "(a (q) (c (q . 80) 1))"
    solution = "9a7461696c20736f6c7574696f6e20666f72206361742074657374"  # opc "'tail solution for cat test'"
    amount = 13
    fee = 100  # mojos

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        await cmd_func(
            tail_as_hex,
            args_to_curry,
            solution,
            self_address,
            amount,
            fee,
            [],
            None,
            [],
            fingerprint,
            signature=[],
            spend=[],
            as_bytes=False,
            select_coin=True,
            quiet=False,
            push=False,
            root_path=root_path,
            wallet_rpc_port=wallet_service_0.rpc_server.webserver.listen_port,
        )

    expected_str_value = (
        '{\n    "amount": 250000000000,\n    '
        '"parent_coin_info": "0x27ae41e4649b934ca495991b7852b85500000000000000000000000000000002",\n    '
        '"puzzle_hash": "0x3ecfd2611925541707c96e689bd415f1991f018a5179d0a7072226d81453d377"\n}\n'
        "Name: 1ef743aa7bd56cec3a65115eb37b6e2b969377eca8c9099337381471efe26e78\n"
    )

    assert f.getvalue() == expected_str_value
    f.truncate(0)

    with contextlib.redirect_stdout(f):
        await cmd_func(
            tail_as_hex,
            args_to_curry,
            solution,
            self_address,
            amount,
            fee,
            [],
            None,
            [],
            fingerprint,
            signature=[],
            spend=[],
            as_bytes=True,
            select_coin=False,
            quiet=True,
            push=False,
            root_path=root_path,
            wallet_rpc_port=wallet_service_0.rpc_server.webserver.listen_port,
        )
    assert expected_tail in f.getvalue()
    assert solution in f.getvalue()

    f.truncate(0)

    with contextlib.redirect_stdout(f):
        await cmd_func(
            tail_as_hex,
            args_to_curry,
            solution,
            self_address,
            amount,
            fee,
            [],
            None,
            [],
            fingerprint,
            signature=[],
            spend=[],
            as_bytes=True,
            select_coin=False,
            quiet=True,
            push=True,
            root_path=root_path,
            wallet_rpc_port=wallet_service_0.rpc_server.webserver.listen_port,
        )

    await full_node_api.process_coin_spends(
        coins={
            Coin(
                bytes32.from_hexstr("1ef743aa7bd56cec3a65115eb37b6e2b969377eca8c9099337381471efe26e78"),
                bytes32.from_hexstr("bebd0c1c65d72e260ff7bef6edc93154568f699c18ced593b585d4a6d5c28ed2"),
                uint64(13),
            )
        }
    )
    await full_node_api.wait_for_wallet_synced(wallet_node=wallet_node_0, timeout=20)
    assert len(wallet_node_0.wallet_state_manager.wallets) == 2
