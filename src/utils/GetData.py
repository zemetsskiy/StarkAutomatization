from random import shuffle, uniform, choice

from src.utils.Info import TokenAmount, ContractInfo
from src.utils.Client import Client
from src.config.logger import logger


async def GetDataForSwap(client: Client, SWAP_PERCENTAGE, swap_to_eth=False):
    try:
        ETH = ContractInfo.ETH.get('address')
        USDT = ContractInfo.USDT.get('address')
        USDC = ContractInfo.USDC.get('address')
        DAI = ContractInfo.DAI.get('address')

        tokens_list = [ETH, USDC, USDT, DAI]

        if swap_to_eth:
            to_token = ETH
            to_token_name = 'ETH'
            to_token_address = ETH
            tokens_list.remove(ETH)
            SWAP_PERCENTAGE = 100
        else:
            shuffle(tokens_list)
            to_token = choice(tokens_list)
            to_token_data = ContractInfo.GetData(to_token)
            to_token_name = to_token_data.get('name')
            to_token_address = to_token_data.get('address')
            tokens_list.remove(to_token)

        from_token_data = ContractInfo.GetData(choice(tokens_list))
        from_token_address = from_token_data.get('address')
        from_token_name = from_token_data.get('name')
        from_token_decimals = from_token_data.get('decimals')
        balance_first_token = 0

        for from_token_address_ in tokens_list:
            balance_first_token = await client.get_balance(token_address=from_token_address_,
                                                           decimals=ContractInfo.GetData(from_token_address_).get('decimals'))
            if balance_first_token.Wei > 0:
                from_token_address = from_token_address_
                from_token_name = ContractInfo.GetData(from_token_address).get('name')
                from_token_decimals = ContractInfo.GetData(from_token_address).get('decimals')
                break
            else:
                balance_first_token = TokenAmount(amount=0)

        from_token_amount = float(balance_first_token.Ether) * (SWAP_PERCENTAGE / 100)

        amount = TokenAmount(
            amount=round(from_token_amount, from_token_decimals),
            decimals=from_token_decimals)

        if amount.Ether > 0:
            return {
                    'amount': amount,
                    'to_token_address': to_token_address,
                    'to_token_name': to_token_name,
                    'from_token_address': from_token_address,
                    'from_token_name': from_token_name,
                    'from_token_decimals': from_token_decimals
                    }
    except Exception as err:
        if "Cannot connect to host starknet-mainnet.infura.io" in str(err):
            raise ValueError("Some problems with rpc. Cannot connect to host starknet-mainnet.infura.io")
        else:
            logger.error(f"[{client.address_to_log}] Error while getting data for swap: {err}")


async def GetDataForLP(client: Client, dex, JEDISWAP_LIQ_PERCENTAGE):
    global token_one_name, token_two_name
    try:
        ETH_ADDRESS = ContractInfo.ETH.get('address')
        USDT_ADDRESS = ContractInfo.USDT.get('address')
        USDC_ADDRESS = ContractInfo.USDC.get('address')
        tokens_list = [ETH_ADDRESS, USDC_ADDRESS, USDT_ADDRESS]

        #from_token = choice(tokens_list)
        from_token = ETH_ADDRESS
        tokens_list.remove(from_token)
        to_token = choice(tokens_list)
        tokens_list.remove(to_token)
        #to_token = USDC_ADDRESS

        token_one_data = ContractInfo.GetData(from_token)
        token_two_data = ContractInfo.GetData(to_token)

        token_one_address = token_one_data.get('address')
        token_two_address = token_two_data.get('address')

        token_one_decimals = token_one_data.get('decimals')
        token_two_decimals = token_two_data.get('decimals')

        pooled_token_data = {}
        amount_one = 0
        amount_two = 0
        amount_in_usdt = 0

        # ETH/USDT pool
        if (token_one_address == ETH_ADDRESS and token_two_address == USDT_ADDRESS) or (token_one_address == USDT_ADDRESS and token_two_address == ETH_ADDRESS):
            if dex == 'jediswap':
                pooled_token_data = ContractInfo.GetData(0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6)
            token_one_name = 'ETH'
            token_one_address = ETH_ADDRESS
            token_one_decimals = 18
            token_two_name = 'USDT'
            token_two_address = USDT_ADDRESS
            token_two_decimals = 6

        elif (token_one_address == ETH_ADDRESS and token_two_address == USDC_ADDRESS) or (token_one_address == USDC_ADDRESS and token_two_address == ETH_ADDRESS):
            if dex == 'jediswap':
                pooled_token_data = ContractInfo.GetData(0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a)
            token_one_name = 'ETH'
            token_one_address = ETH_ADDRESS
            token_one_decimals = 18
            token_two_name = 'USDC'
            token_two_address = USDC_ADDRESS
            token_two_decimals = 6

        elif (token_one_address == USDT_ADDRESS and token_two_address == USDC_ADDRESS) or (token_one_address == USDC_ADDRESS and token_two_address == USDT_ADDRESS):
            if dex == 'jediswap':
                pooled_token_data = ContractInfo.GetData(0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b)
            token_one_name = 'USDC'
            token_one_address = USDC_ADDRESS
            token_one_decimals = 6
            token_two_name = 'USDT'
            token_two_address = USDT_ADDRESS
            token_two_decimals = 6

        pooled_token_address = pooled_token_data.get('address')
        pooled_token_name = pooled_token_data.get('name')
        balanceOf_first = await client.get_balance(token_address=token_one_address, decimals=token_one_decimals)
        balanceOf_second = await client.get_balance(token_address=token_two_address, decimals=token_two_decimals)

        if balanceOf_second.Wei <= 0 or balanceOf_first.Wei <= 0:
            logger.error(f"balanceOf_second {token_two_name} {balanceOf_second.Wei}. balanceOf_first {token_one_name} {balanceOf_first.Wei}")
            raise ValueError("Insufficient tokens on balance to add a liquidity pair. Only ETH is available")

        if token_one_name == 'ETH':
            eth_price = client.get_eth_price()
            eth_in_usd = float(balanceOf_first.Ether) * eth_price
            usd_in_crypto = float(balanceOf_second.Ether)
            min_balance = (min(eth_in_usd, usd_in_crypto)) * JEDISWAP_LIQ_PERCENTAGE / 100
            amount_in_usdt = uniform(0.1, float(min_balance))
            amount_one = TokenAmount(amount=(float(amount_in_usdt) / eth_price))
            amount_two = TokenAmount(amount=eth_price * float(amount_one.Ether), decimals=6)
        elif (token_one_name == 'USDT' and token_two_name == 'USDC') or (token_one_name == 'USDC' and token_two_name == 'USDT'):
            amount_in_usdt = uniform(0.1, float(min([balanceOf_first.Ether, balanceOf_second.Ether]) * JEDISWAP_LIQ_PERCENTAGE / 100))
            token_one_address = USDT_ADDRESS
            token_two_address = USDC_ADDRESS
            amount_one = amount_in_usdt
            amount_two = amount_in_usdt

        if amount_one and amount_two and amount_in_usdt:
            return {
                    'pooled_token_address': pooled_token_address,
                    'pooled_token_name': pooled_token_name,
                    'amount_one': amount_one,
                    'amount_two': amount_two,
                    'amount_in_usdt': amount_in_usdt,
                    'token_one_address': token_one_address,
                    'token_two_address': token_two_address,
                    'token_one_name': token_one_name,
                    'token_two_name': token_two_name,
                    'token_one_decimals': token_one_decimals,
                    'token_two_decimals': token_two_decimals
                    }
    except Exception as err:
        raise ValueError(f"[{client.address_to_log}] Error while getting data for adding liquidity: {err}")