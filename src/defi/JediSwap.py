import asyncio
import random
from time import time

from src.utils.Client import Client
from src.utils.GetData import GetDataForSwap, GetDataForLP
from src.utils.Info import TokenAmount, ContractInfo
from src.config.logger import logger
from starknet_py.contract import Contract


class JediSwap:

    ETH_ADDRESS = ContractInfo.ETH.get('address')
    ETH_ABI = ContractInfo.ETH.get('abi')

    USDT_ADDRESS = ContractInfo.USDT.get('address')
    USDT_ABI = ContractInfo.USDT.get('abi')

    USDC_ADDRESS = ContractInfo.USDC.get('address')
    USDC_ABI = ContractInfo.USDC.get('abi')

    DAI_ADDRESS = ContractInfo.DAI.get('address')
    DAI_ABI = ContractInfo.DAI.get('abi')

    JEDISWAP_CONTRACT = ContractInfo.JEDISWAP.get('address')
    JEDISWAP_ABI = ContractInfo.JEDISWAP.get('abi')

    JEDISWAP_ETHUSDC_CONTRACT_ADDRESS = ContractInfo.JEDISWAP_ETHUSDC.get('address')
    JEDISWAP_ETHUSDC_CONTRACT_ABI = ContractInfo.JEDISWAP_ETHUSDC.get('abi')

    JEDISWAP_ETHUSDT_CONTRACT_ADDRESS = ContractInfo.JEDISWAP_ETHUSDT.get('address')
    JEDISWAP_ETHUSDT_CONTRACT_ABI = ContractInfo.JEDISWAP_ETHUSDT.get('abi')

    JEDISWAP_USDCUSDT_CONTRACT_ADDRESS = ContractInfo.JEDISWAP_USDCUSDT.get('address')
    JEDISWAP_USDCUSDT_CONTRACT_ABI = ContractInfo.JEDISWAP_USDCUSDT.get('abi')

    def __init__(self, client: Client, JEDISWAP_SWAP_PERCENTAGE, JEDISWAP_LIQ_PERCENTAGE, SLIPPAGE):
        self.client = client
        self.contract = Contract(address=JediSwap.JEDISWAP_CONTRACT, abi=JediSwap.JEDISWAP_ABI, provider=self.client.account)
        self.swap_percentage = JEDISWAP_SWAP_PERCENTAGE
        self.liq_percentage = JEDISWAP_LIQ_PERCENTAGE
        self.slippage = SLIPPAGE

    async def swap(self, swap_to_eth=False):
        try:
            global min_to_amount
            #min_amount = 0

            data_for_swap = await GetDataForSwap(client=self.client, SWAP_PERCENTAGE=self.swap_percentage, swap_to_eth=swap_to_eth)

            if data_for_swap == {}:
                return False

            amount, to_token_address, to_token_name, from_token_address, from_token_name, from_token_decimals = data_for_swap.values()

            logger.info(f"[{self.client.address_to_log}] Swapping {amount.Ether} {from_token_name} to {to_token_name} [JediSwap]")
            is_approved = await self.client.approve_interface(token_address=from_token_address,
                                                              spender=JediSwap.JEDISWAP_CONTRACT,
                                                              decimals=from_token_decimals, amount=amount)

            # if is_approved:
            #     eth_price = Client.get_eth_price()
            #     if to_token_name == 'USDT' or to_token_name == 'USDC':
            #         if from_token_name == 'ETH':
            #             min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - self.slippage / 100), decimals=6)
            #             min_amount = min_to_amount
            #         elif from_token_name == 'DAI':
            #             min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - self.slippage / 100), decimals=6)
            #             min_amount = min_to_amount
            #
            #     elif to_token_name == 'ETH':
            #         min_to_amount = TokenAmount(amount=float(amount.Ether) / eth_price * (1 - self.slippage / 100), decimals=18)
            #         min_amount = min_to_amount
            #
            #     elif to_token_name == 'DAI':
            #         if from_token_name == 'USDT' or from_token_name == 'USDC':
            #             min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - self.slippage / 100), decimals=18)
            #             min_amount = min_to_amount
            #
            #         elif from_token_name == 'ETH':
            #             min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - self.slippage / 100), decimals=18)
            #             min_amount = min_to_amount
            if is_approved:
                eth_price = self.client.get_eth_price()
                if to_token_name == 'USDT' or to_token_name == 'USDC':
                    if from_token_name == 'ETH':
                        min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - self.slippage / 100),
                                                    decimals=6)
                    elif from_token_name == 'DAI':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - self.slippage / 100),
                                                    decimals=6) \

                    elif from_token_name == 'USDT' or from_token_name == 'USDC':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - self.slippage / 100), decimals=18)

                elif to_token_name == 'ETH':
                    min_to_amount = TokenAmount(amount=float(amount.Ether) / eth_price * (1 - self.slippage / 100),
                                                decimals=18)
                elif to_token_name == 'DAI':
                    if from_token_name == 'USDT' or from_token_name == 'USDC':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - self.slippage / 100), decimals=18)
                    elif from_token_name == 'ETH':
                        min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - self.slippage / 100),
                                                    decimals=18)

                # tx_hash = await self.client.send_transaction(interacted_contract=self.contract,
                #                                              function_name='swap_exact_tokens_for_tokens',
                #                                              amountIn=int(amount.Wei * 0.99),
                #                                              amountOutMin=min_to_amount.Wei,
                #                                              path=[from_token_address, to_token_address],
                #                                              to=self.client.address,
                #                                              deadline=int(time() + 3600))
                print(int(amount.Wei * 0.99))
                print(min_to_amount.Wei)
                print(from_token_address)
                print(to_token_address)
                print(self.client.address)
                print(int(time() + 3600))

                tx_hash = await self.client.call(interacted_contract_address=JediSwap.JEDISWAP_CONTRACT,
                                                 calldata=[
                                                     int(amount.Wei * 0.99),
                                                     0,
                                                     min_to_amount.Wei,
                                                     0,
                                                     2,
                                                     from_token_address,
                                                     to_token_address,
                                                     self.client.address,
                                                     int(time() + 3600)
                                                    ],
                                                 selector_name='swap_exact_tokens_for_tokens')

                if tx_hash:
                    logger.info(f"[{self.client.address_to_log}] Successfully swapped {amount.Ether} {from_token_name} to {min_to_amount.Ether} {to_token_name} [JediSwap]")
                    return True
        except Exception as err:
            if "Contract not found" in str(err):
                raise ValueError("Seems contract (address) is not deployed yet because it did not have any txs before [JediSwap]")
            elif "nonce" in str(err):
                raise ValueError("Invalid transaction nonce [JediSwap]")
            elif "Cannot connect to host" in str(err):
                raise ValueError("Some problems with rpc. Cannot connect to host starknet-mainnet.infura.io [JediSwap]")
            elif "Transaction reverted: Error in the called contract." in str(err):
                raise ValueError(str(err))
            else:
                raise ValueError(f"{str(err)} [JediSwap]")

    async def add_liquidity(self):
        try:
            data_for_adding_liquidity = await GetDataForLP(client=self.client, JEDISWAP_LIQ_PERCENTAGE=self.liq_percentage, dex='jediswap')

            lp_contract, lp_name, amount_one, amount_two, amount_in_usdt, token_one_address, token_two_address, token_one_name, token_two_name, token_one_decimals, token_two_decimals = data_for_adding_liquidity.values()

            logger.info(f"[{self.client.address_to_log}] Adding liquidity to {lp_name} LP {amount_one.Ether} {token_one_name} [JediSwap]")

            is_approved_one = await self.client.approve_interface(token_address=token_one_address,
                                                              spender=JediSwap.JEDISWAP_CONTRACT,
                                                              decimals=token_one_decimals, amount=amount_one)

            is_approved_two = await self.client.approve_interface(token_address=token_two_address,
                                                              spender=JediSwap.JEDISWAP_CONTRACT,
                                                              decimals=token_two_decimals, amount=amount_two)
            if is_approved_one and is_approved_two:
                tx_hash = await self.client.send_transaction(interacted_contract=self.contract,
                                                             function_name='add_liquidity',
                                                             tokenA=token_one_address,
                                                             tokenB=token_two_address,
                                                             amountADesired=amount_one.Wei,
                                                             amountBDesired=amount_two.Wei,
                                                             amountAMin=int(amount_one.Wei * (1 - self.slippage / 100)),
                                                             amountBMin=int(amount_two.Wei * (1 - self.slippage / 100)),
                                                             to=self.client.address,
                                                             deadline=int(time() + 3600))
                if tx_hash:
                    logger.info(f"[{self.client.address_to_log}] Successfully added ${amount_in_usdt} to {lp_name} LP [JediSwap]")
                    random_sleep = random.randint(30, 90)
                    logger.info(f"[{self.client.address_to_log}] Sleeping for {random_sleep} s before removing liquidity [JediSwap]")
                    await asyncio.sleep(random_sleep)
                    await self.remove_liquidity(lp_contract=lp_contract, amountA=int(amount_one.Wei * (1 - self.slippage / 100)), amountB=int(amount_two.Wei * (1 - self.slippage / 100)))
                    return True
        except Exception as err:
            if "Contract not found" in str(err):
                raise ValueError("Seems contract (address) is not deployed yet because it did not have any txs before [JediSwap]")
            elif "Invalid transaction nonce" in str(err):
                raise ValueError("Invalid transaction nonce")
            elif "Insufficient tokens on balance to add a liquidity pair. Only ETH is available" in str(err):
                raise ValueError("Insufficient tokens on balance to add a liquidity pair. Only ETH is available")
            else:
                raise ValueError(f"{str(err)} [JediSwap]")

    async def remove_liquidity(self, lp_contract, amountA=None, amountB=None):
        global tokenA, tokenB
        try:
            logger.info(f"[{self.client.address_to_log}] Removing liquidity [JediSwap]")
            amount: TokenAmount = await self.client.get_balance(token_address=lp_contract, decimals=18)
            if lp_contract == JediSwap.JEDISWAP_ETHUSDC_CONTRACT_ADDRESS:
                tokenA = JediSwap.ETH_ADDRESS
                tokenB = JediSwap.USDC_ADDRESS
            elif lp_contract == JediSwap.JEDISWAP_ETHUSDT_CONTRACT_ADDRESS:
                tokenA = JediSwap.ETH_ADDRESS
                tokenB = JediSwap.USDT_ADDRESS
            elif lp_contract == JediSwap.JEDISWAP_USDCUSDT_CONTRACT_ADDRESS:
                tokenA = JediSwap.USDC_ADDRESS
                tokenB = JediSwap.USDT_ADDRESS
            is_approved = await self.client.approve_interface(token_address=lp_contract,
                                                              spender=JediSwap.JEDISWAP_CONTRACT,
                                                              decimals=18, amount=amount)
            if is_approved:
                tx_hash = await self.client.send_transaction(interacted_contract=self.contract,
                                                             function_name='remove_liquidity',
                                                             tokenA=tokenA,
                                                             tokenB=tokenB,
                                                             liquidity=amount.Wei,
                                                             amountAMin=amountA,
                                                             amountBMin=amountB,
                                                             to=self.client.address,
                                                             deadline=int(time() + 3600))
                if tx_hash:
                    logger.info(f"[{self.client.address_to_log}] Successfully removed liquidity [JediSwap]")
                    return True
        except Exception as err:
            if "Contract not found" in str(err):
                raise ValueError("Seems contract (address) is not deployed yet because it did not have any txs before [JediSwap]")
            elif "Invalid transaction nonce" in str(err):
                raise ValueError("Invalid transaction nonce")
            else:
                logger.error(f"[{self.client.address_to_log}] Error while removing $ from LP: {err} [JediSwap]")
                raise ValueError(f"{str(err)} [JediSwap]")
