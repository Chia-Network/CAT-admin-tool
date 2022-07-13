import aiohttp
from typing import Optional

from chia.cmds.wallet_funcs import get_wallet
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.config import load_config
from chia.util.ints import uint16


# Loading the client requires the standard chia root directory configuration that all of the chia commands rely on
async def get_client() -> Optional[WalletRpcClient]:
    try:
        config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
        self_hostname = config["self_hostname"]
        full_node_rpc_port = config["wallet"]["rpc_port"]
        full_node_client = await WalletRpcClient.create(
            self_hostname, uint16(full_node_rpc_port), DEFAULT_ROOT_PATH, config
        )
        return full_node_client
    except Exception as e:
        if isinstance(e, aiohttp.ClientConnectorError):
            print(
                f"Connection error. Check if full node is running at {full_node_rpc_port}"
            )
        else:
            print(f"Exception from 'harvester' {e}")
        return None


async def get_signed_tx(fingerprint, ph, amt, fee):
    try:
        wallet_client: WalletRpcClient = await get_client()
        wallet_client_f, _ = await get_wallet(wallet_client, fingerprint)
        return await wallet_client_f.create_signed_transaction(
            [{"puzzle_hash": ph, "amount": amt}], fee=fee
        )
    finally:
        wallet_client.close()
        await wallet_client.await_closed()
