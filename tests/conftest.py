from __future__ import annotations

import pytest_asyncio
from chia._tests.util.setup_nodes import setup_simulators_and_wallets_service
from chia.simulator.block_tools import test_constants


@pytest_asyncio.fixture(scope="function")
async def one_wallet_and_one_simulator_services():  # type: ignore[no-untyped-def]
    async with setup_simulators_and_wallets_service(1, 1, test_constants) as _:
        yield _
