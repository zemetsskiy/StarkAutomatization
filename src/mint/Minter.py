import random
from random import uniform, randint

from src.utils.Client import Client
from src.utils.Info import ContractInfo, TokenAmount
from src.config.logger import logger
from starknet_py.contract import Contract


class Minter:
    def __init__(self, client: Client):
        self.client = client

    async def mintStarkVerse(self):
        try:
            contract_address = ContractInfo.STARKVERSE.get('address')
            abi = ContractInfo.STARKVERSE.get('abi')
            contract = Contract(address=contract_address, abi=abi, provider=self.client.account)

            logger.info(f"[{self.client.address_to_log}] Minting nft [StarkVerse NFT]")

            # tx_hash = await self.client.send_transaction(interacted_contract=contract,
            #                                              function_name='publicMint',
            #                                              to=self.client.address
            #                                              )

            tx_hash = await self.client.call(interacted_contract_address=contract_address,
                                             calldata=[self.client.address],
                                             selector_name='publicMint')

            if tx_hash:
                logger.info(
                    f"[{self.client.address_to_log}] Successfully minted [StarkVerse NFT]")
                return True
        except Exception as err:
            if "Contract not found" in str(err):
                logger.error(f"[{self.client.address_to_log}] Seems contract (address) is not deployed yet because it did not have any txs before")
            elif "Invalid transaction nonce" in str(err):
                raise ValueError("Invalid transaction nonce")
            else:
                logger.error(f"[{self.client.address_to_log}] Error while minting: {err} [StarkVerse NFT]")

    async def mintStarknetIdNFT(self):
        try:
            contract_address = ContractInfo.STARKNETIDNFT.get('address')
            abi = ContractInfo.STARKNETIDNFT.get('abi')
            contract = Contract(address=contract_address, abi=abi, provider=self.client.account)

            logger.info(f"[{self.client.address_to_log}] Minting nft [Starknet.id Identity NFT]")

            id = random.randint(0, 2**128 - 1)

            max_fee = TokenAmount(amount=float(uniform(0.0007534534534, 0.001)))
            #
            # prepared_call = contract.functions["mint"].prepare(id, max_fee=int(max_fee.Wei * (1 + randint(15, 30) / 100)))
            # await prepared_call.invoke()

            tx_hash = await self.client.call(interacted_contract_address=contract_address,
                                             calldata=[id],
                                             selector_name='mint')

            logger.info(f"[{self.client.address_to_log}] Successfully minted [Starknet.id Identity NFT]")
            return True
        except Exception as err:
            if "Contract not found" in str(err):
                logger.error(f"[{self.client.address_to_log}] Seems contract (address) is not deployed yet because did it not have any txs before [Starknet.id Identity NFT]")
            elif "Invalid transaction nonce" in str(err):
                raise ValueError("Invalid transaction nonce")
            else:
                logger.error(f"[{self.client.address_to_log}] Error while swapping: {err} [Starknet.id Identity NFT]")
