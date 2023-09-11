import asyncio
import re

from web3 import Web3

from src.config.logger import logger
from src.utils.Info import ContractInfo


class Bridger:
    ETH_RPC = "https://eth-mainnet.public.blastapi.io"

    @staticmethod
    def get_balance(pk):
        web3 = Web3(Web3.HTTPProvider(Bridger.ETH_RPC))
        wallet_address = web3.eth.account.from_key(pk).address
        balance = web3.eth.get_balance(Web3.to_checksum_address(wallet_address))
        return balance / 1e18

    @staticmethod
    def address_from_pk(pk):
        web3 = Web3(Web3.HTTPProvider(Bridger.ETH_RPC))
        wallet_address = web3.eth.account.from_key(pk).address
        return wallet_address

    @staticmethod
    async def bridge_eth_stark(pk, amount_to_bridge, l2Recipient, MAX_GWEI):
        try:
            web3 = Web3(Web3.HTTPProvider(Bridger.ETH_RPC))
            wallet_address = web3.eth.account.from_key(pk).address

            bridge_contract = web3.eth.contract(
                address=Web3.to_checksum_address(ContractInfo.BRIDGE.get('address')),
                abi=ContractInfo.BRIDGE.get('abi'))

            while web3.eth.gas_price / 1e9 > MAX_GWEI:
                logger.info(f"Current gas price ({round(web3.eth.gas_price / 1e9, 2)} GWEI) is higher than MAX_GWEI ({MAX_GWEI} GWEI). Waiting for it to decrease...")
                await asyncio.sleep(15)

            nonce = web3.eth.get_transaction_count(wallet_address)

            estimated_gas = bridge_contract.functions.deposit(
                amount=Web3.to_wei(amount_to_bridge, 'ether'),
                l2Recipient=l2Recipient
            ).estimate_gas({
                'from': wallet_address,
                'value': Web3.to_wei(amount_to_bridge + 0.00003, 'ether'),
                'nonce': nonce,
            })

            tx = bridge_contract.functions.deposit(
                amount=Web3.to_wei(amount_to_bridge, 'ether'),
                l2Recipient=l2Recipient
            ).build_transaction(
                {
                    'from': wallet_address,
                    'gas': estimated_gas,
                    'value': Web3.to_wei(amount_to_bridge+0.00003, 'ether'),
                    'nonce': nonce,
                    'gasPrice': web3.eth.gas_price
                })

            signed_tx = web3.eth.account.sign_transaction(tx, pk)
            raw_tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            bridge_tx_hash = web3.to_hex(raw_tx_hash)

            for i in range(5):
                await asyncio.sleep(15)
                try:
                    bridge_tx_receipt = web3.eth.get_transaction_receipt(raw_tx_hash)
                    if bridge_tx_receipt.status == 1:
                        logger.info(f"Bridged {round(amount_to_bridge, 4)}ETH successfully [Bridge]")
                        logger.info(f"Tx: https://etherscan.io/tx/{bridge_tx_hash}")
                        return True
                    else:
                        logger.error(f"Something went wrong while bridging {amount_to_bridge}ETH to Starknet [Bridge]")
                        continue
                except Exception as err:
                    if i == 4:
                        logger.error(f"Exception raised while bridging - {str(err)} [Bridge]")
                        return str(err)
                    else:
                        continue

        except Exception as err:
            error_message = str(err)
            match = re.search(r'address (\w+) have (\d+) want (\d+)', error_message)

            if match:
                address, have_wei, want_wei = match.groups()
                have_eth = int(have_wei) / 1e18
                want_eth = int(want_wei) / 1e18
                diff_eth = want_eth - have_eth
                logger.error(f"{address} has insufficient funds. Currently have: {have_eth:.5f} ETH. Required: {want_eth:.5f} ETH. You need to add {diff_eth:.5f} ETH.")
                return error_message
            else:
                logger.error(error_message)
                return error_message