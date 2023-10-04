import pytest_asyncio

from chia.simulator.block_tools import test_constants
from chia.simulator.setup_nodes import setup_simulators_and_wallets_service

@pytest_asyncio.fixture(scope="function")
async def one_wallet_and_one_simulator_services():
    async with setup_simulators_and_wallets_service(1, 1, test_constants) as _:
        yield _
