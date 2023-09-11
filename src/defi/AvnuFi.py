from starknet_py.contract import Contract

from src.utils.GetData import GetDataForSwap
from src.utils.Client import Client
from src.utils.Info import ContractInfo, TokenAmount

from src.config.logger import logger


class AvnuFi:
    AVNUFI_CONTRACT_ADDRESS = ContractInfo.AVNUFI.get('address')
    AVNUFI_ABI = ContractInfo.AVNUFI.get('abi')

    def __init__(self, client: Client, AVNUFI_SWAP_PERCENTAGE, SLIPPAGE):
        self.client = client
        self.contract = Contract(address=AvnuFi.AVNUFI_CONTRACT_ADDRESS, abi=AvnuFi.AVNUFI_ABI, provider=self.client.account)
        self.percentage = AVNUFI_SWAP_PERCENTAGE
        self.slippage = SLIPPAGE

    async def swap(self, swap_to_eth=False, data_for_swap=None):
        try:
            router = ContractInfo.JEDISWAP.get('address')

            global min_amount
            min_amount = 0

            if not data_for_swap:
                data_for_swap = await GetDataForSwap(client=self.client, SWAP_PERCENTAGE=self.percentage, swap_to_eth=swap_to_eth)

            if data_for_swap == {}:
                return False

            amount, to_token_address, to_token_name, from_token_address, from_token_name, from_token_decimals = data_for_swap.values()

            logger.info(f"[{self.client.address_to_log}] Swapping {amount.Ether} {from_token_name} to {to_token_name} [AvnuFi]")
            is_approved = await self.client.approve_interface(
                                                              token_address=from_token_address,
                                                              spender=AvnuFi.AVNUFI_CONTRACT_ADDRESS,
                                                              decimals=from_token_decimals, amount=amount
                                                            )
            if is_approved:
                eth_price = self.client.get_eth_price()
                if to_token_name == 'USDT' or to_token_name == 'USDC':
                    if from_token_name == 'ETH':
                        min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - self.slippage / 100),
                                                    decimals=6)
                        min_amount = min_to_amount

                    elif from_token_name == 'DAI':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - self.slippage / 100),
                                                    decimals=6)
                        min_amount = min_to_amount

                elif to_token_name == 'ETH':
                    min_to_amount = TokenAmount(amount=float(amount.Ether) / eth_price * (1 - self.slippage / 100), decimals=18)
                    min_amount = min_to_amount

                elif to_token_name == 'DAI':
                    if from_token_name == 'USDT' or from_token_name == 'USDC':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - self.slippage / 100), decimals=18)
                        min_amount = min_to_amount

                    elif from_token_name == 'ETH':
                        min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - self.slippage / 100), decimals=18)
                        min_amount = min_to_amount

                tx_hash = await self.client.call(interacted_contract_address=AvnuFi.AVNUFI_CONTRACT_ADDRESS,
                                                 calldata=[
                                                     from_token_address,
                                                     int(amount.Wei * 0.99),
                                                     0,
                                                     to_token_address,
                                                     min_amount.Wei,
                                                     0,
                                                     min_amount.Wei,
                                                     0,
                                                     self.client.address,
                                                     0,
                                                     0,
                                                     1,
                                                     from_token_address,
                                                     to_token_address,
                                                     router,
                                                     0x64
                                                 ],
                                                 selector_name='multi_route_swap')
                if tx_hash:
                    logger.info(f"[{self.client.address_to_log}] Successfully swapped {amount.Ether} {from_token_name} to {min_amount.Ether} {to_token_name} [AvnuFi]")
                    return True
        except Exception as err:
            if "Contract not found" in str(err):
                logger.error(f"[{self.client.address_to_log}] Seems contract (address) is not deployed yet because it did not have any txs before [AvnuFi]")
            elif "Invalid transaction nonce" in str(err):
                raise ValueError("Invalid transaction nonce")
            else:
                logger.error(f"[{self.client.address_to_log}] Error while swapping: {err} [AvnuFi]")
