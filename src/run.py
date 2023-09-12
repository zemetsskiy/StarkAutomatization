import yaml

from pathlib import Path
from asyncio import (sleep, create_task, gather)
from random import randint, shuffle
from src.utils.Client import Client
from src.utils.GetAccs import KEYS_LIST
from src.defi.JediSwap import JediSwap
from src.defi.AvnuFi import AvnuFi
from src.defi.TenkSwap import TenkSwap
from src.defi.Dmail import Dmail
from src.mint.Minter import Minter
from src.cex.Binance import Binance
from src.bridge.Bridger import Bridger
from src.config.logger import logger


def get_settings():
    current_dir = Path(__file__).parent

    file_path = current_dir.parent / "settings.yaml"

    if file_path.exists():
        try:
            with file_path.open('r') as file:
                settings = yaml.safe_load(file)
            return settings
        except Exception as err:
            if "while scanning a simple key" in str(err):
                logger.error("You made an error while filling settings.yaml file")
            else:
                logger.error(f"Error reading {file_path}: {err}")
    else:
        logger.error(f"Settings file {file_path} was not found.")


async def setup_acc(keys):
    global formatted_key
    try:
        TASKS = []

        public_key = ""
        private_key = ""
        evm_private_key = ""
        split_keys = keys.split(':')

        if len(split_keys) == 2:
            public_key, private_key = split_keys
        elif len(split_keys) == 3:
            public_key, private_key, evm_private_key = split_keys

        address = int(public_key, 16)

        settings = get_settings()

        MAX_GWEI = settings['basic']['max-gwei']
        SWAP_SLIPPAGE = settings['basic']['swap-slippage']
        MIN_RANDOM_DELAY = settings['basic']['min-random-delay-between-actions']
        MAX_RANDOM_DELAY = settings['basic']['max-random-delay-between-actions']

        BINANCE_API_KEY = settings['api']['binance-api-key']
        BINANCE_SECRET_KEY = settings['api']['binance-secret-key']
        STARKNET_RPC = settings['api']['starknet-rpc']

        STARKGATE_BRIDGE = settings['deposit']['starkgate-bridge']
        BRIDGE_AMOUNT_PERCENTAGE = settings['deposit']['bridge-amount-percentage']
        BINANCE_WITHDRAW = settings['deposit']['binance-withdraw-on']
        BALANCE_TO_WITHDRAW = settings['deposit']['balance-to-withdraw']

        JEDISWAP_SWAP_COUNT = settings['actions']['jediswap-swap']
        JEDISWAP_LP_COUNT = settings['actions']['jediswap-liq-add-remove']
        AVNUFI_SWAP_COUNT = settings['actions']['avnufi-swap']
        TENKSWAP_SWAP_COUNT = settings['actions']['10kswap-swap']
        STARKVERSE_NFT_MINT_COUNT = settings['actions']['starkverse-nft-mint']
        STARKNETID_NFT_MINT_COUNT = settings['actions']['starknetid-nft-mint']
        JEDISWAP_SWAP_PERCENTAGE = settings['actions']['jediswap-swap-percentage']
        JEDISWAP_LIQ_PERCENTAGE = settings['actions']['jediswap-liq-percentage']

        AVNUFI_SWAP_PERCENTAGE = settings['actions']['avnufi-swap-percentage']
        TENK_SWAP_PERCENTAGE = settings['actions']['10kswap-swap-percentage']

        DMAIL_MIN_MESSAGES_COUNT = settings['actions']['dmail-min-messages-count']
        DMAIL_MAX_MESSAGES_COUNT = settings['actions']['dmail-max-messages-count']

        #SWAP_ALL_TO_ETH = settings['actions']['swap-all-tokens-to-eth-at-the-end']

        client = Client(address=address, private_key=int(private_key, 16), address_to_log=public_key, starknet_rpc=STARKNET_RPC, MAX_GWEI=MAX_GWEI)

        if isinstance(JEDISWAP_SWAP_COUNT, int) and JEDISWAP_SWAP_COUNT != 0:
            JediSwap_client = JediSwap(client=client, JEDISWAP_SWAP_PERCENTAGE=JEDISWAP_SWAP_PERCENTAGE, JEDISWAP_LIQ_PERCENTAGE=JEDISWAP_LIQ_PERCENTAGE, SLIPPAGE=SWAP_SLIPPAGE)
            for _ in range(JEDISWAP_SWAP_COUNT):
                TASKS.append(JediSwap_client.swap)

        if isinstance(AVNUFI_SWAP_COUNT, int) and AVNUFI_SWAP_COUNT != 0:
            AvnuFi_client = AvnuFi(client=client, AVNUFI_SWAP_PERCENTAGE=AVNUFI_SWAP_PERCENTAGE, SLIPPAGE=SWAP_SLIPPAGE)
            for _ in range(AVNUFI_SWAP_COUNT):
                TASKS.append(AvnuFi_client.swap)

        if isinstance(TENKSWAP_SWAP_COUNT, int) and TENKSWAP_SWAP_COUNT != 0:
            TenkSwap_client = TenkSwap(client=client, TENK_SWAP_PERCENTAGE=TENK_SWAP_PERCENTAGE, SLIPPAGE=SWAP_SLIPPAGE)
            for _ in range(TENKSWAP_SWAP_COUNT):
                TASKS.append(TenkSwap_client.swap)

        if isinstance(STARKVERSE_NFT_MINT_COUNT, int) and STARKVERSE_NFT_MINT_COUNT != 0:
            Minter_client = Minter(client=client)
            for _ in range(STARKVERSE_NFT_MINT_COUNT):
                TASKS.append(Minter_client.mintStarkVerse)

            if isinstance(STARKNETID_NFT_MINT_COUNT, int) and STARKNETID_NFT_MINT_COUNT != 0:
                for _ in range(STARKNETID_NFT_MINT_COUNT):
                    TASKS.append(Minter_client.mintStarknetIdNFT)

        global dmail_quantity
        dmail_quantity = 0

        if DMAIL_MIN_MESSAGES_COUNT != 0 and DMAIL_MAX_MESSAGES_COUNT != 0:
            Dmail_client = Dmail(client=client)
            dmail_quantity = randint(DMAIL_MIN_MESSAGES_COUNT, DMAIL_MAX_MESSAGES_COUNT)
            for _ in range(dmail_quantity):
                TASKS.append(Dmail_client.send_message)

        shuffle(TASKS)
        # tasks_quantity = (len(TASKS)+JEDISWAP_LP_COUNT) if JEDISWAP_LP_COUNT else len(TASKS)
        formatted_key = f"{public_key[:5]}...{public_key[-5:]}"
        # logger.info(f"{formatted_key} - {tasks_quantity} {'task' if tasks_quantity == 1 else 'tasks'} added")
        # logger.info(f"Binance withdraw: {'Yes' if BINANCE_WITHDRAW else 'No'}")
        # logger.info(f"Ethereum -> StarkNet bridge: {'Yes' if STARKGATE_BRIDGE else 'No'}")
        # logger.info(f"JediSwap swaps: {JEDISWAP_SWAP_COUNT}")
        # logger.info(f"JediSwap liquidity adding and removing: {JEDISWAP_LP_COUNT}")
        # logger.info(f"AvnuFi swaps: {AVNUFI_SWAP_COUNT}")
        # logger.info(f"10kswap swaps: {TENKSWAP_SWAP_COUNT}")
        # logger.info(f"Dmail messages: {dmail_quantity}")
        # logger.info(f"StarkVerse NFT mints: {STARKVERSE_NFT_MINT_COUNT}")
        # logger.info(f"StarkNetId NFT mints: {STARKNETID_NFT_MINT_COUNT}")
        # logger.info(f"Swap all tokens to ETH at the end: {'Yes' if SWAP_ALL_TO_ETH else 'No'}")

        if BINANCE_WITHDRAW is True:
            delay = randint(15, 30)
            logger.info(f"{formatted_key} Sleeping for {delay} s before withdrawing cash from Binance")
            await sleep(delay)

            EVM_ADDRESS_TO_BRIDGE_FROM = Bridger.address_from_pk(evm_private_key)
            result = Binance.withdraw_token(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY, address=EVM_ADDRESS_TO_BRIDGE_FROM, amount=BALANCE_TO_WITHDRAW)
            if result is True:
                delay = randint(15, 30)
                logger.info(f"[{formatted_key}] Sleeping for {delay} s after withdrawing cash from Binance")
                await sleep(delay)
            else:
                logger.error(f"[{formatted_key}] Stopped working due to an error while withdrawing funds from Binance")

                with open('wallets-with-withdraw-error.txt', 'a+') as f:
                    f.writelines(f"[{formatted_key}] - {result}\n")
                return

        if STARKGATE_BRIDGE is True:
            if evm_private_key != "":
                if BINANCE_WITHDRAW is not True:
                    delay = randint(15, 30)
                    logger.info(f"[{formatted_key}] Sleeping for {delay} s before bridging to StarkNet")
                    await sleep(delay)

                    BALANCE_ON_EVM = Bridger.get_balance(evm_private_key)
                    amount_to_bridge = (BRIDGE_AMOUNT_PERCENTAGE / 100) * BALANCE_ON_EVM
                    print(f"{amount_to_bridge}")

                    result = await Bridger.bridge_eth_stark(pk=evm_private_key, amount_to_bridge=amount_to_bridge,
                                                            l2Recipient=address, MAX_GWEI=MAX_GWEI)
                    if result is True:
                        delay = randint(60, 70)
                        logger.info(f"[{formatted_key}] Sleeping for {delay} s after bridging to StarkNet")
                        await sleep(delay)
                    else:
                        logger.error(f"[{formatted_key}] Stopped working due to an error while bridging to StarkNet")
                        with open('wallets-with-bridge-error.txt', 'a+') as f:
                            f.writelines(f"[{formatted_key}] - {result}\n")
                        return
                else:
                    delay = randint(15, 30)
                    logger.info(f"[{formatted_key}] Sleeping for {delay} s before bridging to StarkNet")
                    await sleep(delay)

                    amount_to_bridge = (BRIDGE_AMOUNT_PERCENTAGE / 100) * BALANCE_TO_WITHDRAW
                    result = await Bridger.bridge_eth_stark(pk=evm_private_key, amount_to_bridge=amount_to_bridge,
                                                            l2Recipient=address, MAX_GWEI=MAX_GWEI)
                    if result is True:
                        delay = randint(60, 70)
                        logger.info(f"[{formatted_key}] Sleeping for {delay} s after bridging to StarkNet")
                        await sleep(delay)
                    else:
                        logger.error(f"[{formatted_key}] Stopped working due to an error while bridging to StarkNet")
                        with open('wallets-with-bridge-error.txt', 'a+') as f:
                            f.writelines(f"[{formatted_key}] - {result}\n")
                        return
            else:
                logger.error("You should put your evm_private_key as a 3rd param in keys.txt")

        start_delay = randint(30, 60)
        logger.info(f"[{formatted_key}] Sleeping for {start_delay} s before taking off")
        await sleep(start_delay)

        log_counter = 0
        for task in TASKS:
            delay = randint(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)
            if log_counter != 0:
                logger.info(f"[{formatted_key}] Sleeping for {delay} s before doing next task")
                task_delay = randint(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)
                await sleep(task_delay)
            try:
                balance = (await client.get_balance()).Ether
                if balance >= 0.000055:
                    await task()
                    log_counter = 1
                else:
                    logger.error(f"[{formatted_key}] Insufficient funds in StarkNet. Balance: {balance} ETH")
                    break
            except Exception as err:
                if "nonce" in str(err):
                    logger.error(f"[{formatted_key}] Invalid transaction nonce.")
                elif "Insufficient tokens on balance to add a liquidity pair. Only ETH is available" in str(err):
                    logger.error(f"[{formatted_key}] {err}")
                elif "host starknet-mainnet.infura.io" in str(err):
                    logger.error(f"[{formatted_key}] {err}")
                    try:
                        retry_delay = randint(15, 30)
                        logger.info(f"[{formatted_key}] Sleeping for {retry_delay} s before retrying")
                        await sleep(retry_delay)
                        await task()
                    except Exception as retry_err:
                        logger.error(f"[{formatted_key}] Error while retrying task after connection issue: {retry_err}")
                elif "Transaction reverted: Error in the called contract." in str(err):
                    logger.error(f"[{formatted_key}] {err}")
                else:
                    logger.error(f"[{formatted_key}] Error while performing task: {err}")

        if isinstance(JEDISWAP_LP_COUNT, int) and JEDISWAP_LP_COUNT != 0:
            JediSwap_client = JediSwap(client=client, JEDISWAP_SWAP_PERCENTAGE=JEDISWAP_SWAP_PERCENTAGE, JEDISWAP_LIQ_PERCENTAGE=JEDISWAP_LIQ_PERCENTAGE, SLIPPAGE=SWAP_SLIPPAGE)
            try:
                await JediSwap_client.add_liquidity()
            except Exception as err:
                if "nonce" in str(err):
                    logger.error(f"[{formatted_key}] Invalid transaction nonce.")
                elif "Insufficient tokens on balance to add a liquidity pair. Only ETH is available" in str(err):
                    logger.error(f"[{formatted_key}] {err}")
                elif "host starknet-mainnet.infura.io" in str(err):
                    logger.error(f"[{formatted_key}] {err}")
                    try:
                        retry_delay = randint(15, 30)
                        logger.info(f"[{formatted_key}] Sleeping for {retry_delay} s before retrying")
                        await sleep(retry_delay)
                        await JediSwap_client.add_liquidity()
                    except Exception as retry_err:
                        logger.error(f"[{formatted_key}] Error while retrying task after connection issue: {retry_err}")
                elif "Transaction reverted: Error in the called contract." in str(err):
                    logger.error(f"[{formatted_key}] {err}")
                else:
                    logger.error(f"[{formatted_key}] {err}")

        # if SWAP_ALL_TO_ETH is True:
        #     logger.info(f"[{formatted_key}] Swapping all the tokens to ETH")
        #     TenkSwap_client = TenkSwap(client=client, TENK_SWAP_PERCENTAGE=TENK_SWAP_PERCENTAGE, SLIPPAGE=SWAP_SLIPPAGE)
        #     for _ in range(3):
        #         task_delay = randint(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)
        #         logger.info(f"[{formatted_key}] Sleeping for {task_delay} s before doing next swap")
        #         await sleep(task_delay)
        #         try:
        #             await TenkSwap_client.swap(swap_to_eth=True)
        #         except Exception as err:
        #             logger.error(f"[{formatted_key}] Err:  {err}")
        #             continue
    except Exception as err:
        logger.error(f"Unexpected error: {err}. Stopped working ")


async def setup_accs():
    ALL_TASKS = []
    logger.info(f"{len(KEYS_LIST)} accs loaded")
    for keys in KEYS_LIST:
        ALL_TASKS.append(create_task(setup_acc(keys=keys)))
        await sleep(2)
    return ALL_TASKS


async def run():
    await gather(* await setup_accs())