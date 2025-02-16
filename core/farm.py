import asyncio
from random import randint

from core.reqs import get_node_status, get_points, start_node, stop_node, check_in
from utils.file_utils import read_proxies, read_farm, write_filed_account
from utils.private_key_to_wallet import private_key_to_wallet
from configs.config import GET_BALANCE
from utils.log_utils import logger
from account import Account
import db

PRIVATE_KEYS_TO_FARM = read_farm()
PROXIES = read_proxies()

async def process_account(private_key: str, proxy):
    ua = await db.get_ua(private_key_to_wallet(private_key))
    if not ua:
        write_filed_account(private_key)
        logger.error(f"{private_key} | Account doesn't register!")
        return

    account = Account(private_key, ua)

    logger.success(f"{account.wallet_address} | Starting account..")
    await asyncio.sleep(randint(0, 12 * 60 * 60))

    while True:
        await check_in(account, proxy)
        await asyncio.sleep(randint(10, 30))
        if await get_node_status(account, proxy):
            await stop_node(account, proxy)
            await asyncio.sleep(randint(10, 30))
        await start_node(account, proxy)
        await asyncio.sleep(randint(10, 30))
        if GET_BALANCE:
            await db.update_points(account.wallet_address, await get_points(account, proxy))
            logger.info(f"Total points: {(await db.get_total_points())[0]}")
        await asyncio.sleep(randint(10 * 60 * 60, 12 * 60 * 60))

async def start():
    tasks = []
    for private_key, proxy in zip(PRIVATE_KEYS_TO_FARM, PROXIES):
        tasks.append(asyncio.create_task(process_account(private_key, proxy)))
    await asyncio.gather(*tasks)