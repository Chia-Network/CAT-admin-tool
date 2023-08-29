from __future__ import annotations

import pytest_asyncio
from chia.simulator.setup_nodes import setup_simulators_and_wallets_service


@pytest_asyncio.fixture(scope="function")
async def one_wallet_and_one_simulator_services():
    async for _ in setup_simulators_and_wallets_service(1, 1, {}):
        yield _
