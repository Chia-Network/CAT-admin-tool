from __future__ import annotations

import pytest_asyncio

from chia.simulator.block_tools import test_constants
from chia._tests.util.setup_nodes import setup_simulators_and_wallets_service
from chia.wallet.wallet_node import WalletNode
from chia.wallet.wallet_node_api import WalletNodeAPI


@pytest_asyncio.fixture(scope="function")
async def one_wallet_and_one_simulator_services():
    async with setup_simulators_and_wallets_service(1, 1, test_constants) as _:
        yield _
