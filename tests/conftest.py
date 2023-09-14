from __future__ import annotations

from typing import AsyncGenerator, List, Tuple

import pytest_asyncio
from chik.full_node.full_node import FullNode
from chik.server.start_service import Service
from chik.simulator.block_tools import BlockTools
from chik.simulator.full_node_simulator import FullNodeSimulator
from chik.simulator.setup_nodes import setup_simulators_and_wallets_service
from chik.wallet.wallet_node import WalletNode
from chik.wallet.wallet_node_api import WalletNodeAPI


@pytest_asyncio.fixture(scope="function")
async def one_wallet_and_one_simulator_services() -> AsyncGenerator[
    Tuple[
        List[Service[FullNode, FullNodeSimulator]],
        List[Service[WalletNode, WalletNodeAPI]],
        BlockTools,
    ],
    None,
]:
    async for _ in setup_simulators_and_wallets_service(1, 1, {}):
        yield _
