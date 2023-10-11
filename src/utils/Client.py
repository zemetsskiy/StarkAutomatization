import asyncio
import requests
from random import randint, uniform
from typing import Optional, Union
from starknet_py.net.client_errors import ClientError

from starknet_py.net.client_models import Call
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.contract import Contract
from starknet_py.net.signer.stark_curve_signer import KeyPair

from src.config.logger import logger
from src.utils.Info import ContractInfo, TokenAmount


class Client:
    def __init__(self, private_key, address, address_to_log, starknet_rpc, MAX_GWEI):
        self.private_key = private_key
        self.address = address
        self.address_to_log = f"{address_to_log[:5]}...{address_to_log[-5:]}"
        self.max_gwei = MAX_GWEI
        self.account = Account(
            client=FullNodeClient(starknet_rpc),
            address=address,
            key_pair=KeyPair.from_private_key(eval(str(self.private_key))),
            chain=StarknetChainId.MAINNET,
        )

    async def approve(self, token_address, spender, amount_to_approve):
        info = ContractInfo.GetData(token_address)
        abi = info.get('abi')
        token_name = info.get('name')

        logger.info(f"[{self.address_to_log}] Approving {token_name}")

        MAX_RETRIES = 4
        retries = 0

        while retries < MAX_RETRIES:
            try:
                contract = Contract(address=token_address, abi=abi, provider=self.account)

                # tx = await self.account.client.call(interacted_contract_address=contract.address,
                #                                  calldata=[spender, amount_to_approve],
                #                                  selector_name='approve')

                prepared_tx = contract.functions['approve'].prepare(spender=spender, amount=amount_to_approve)
                fee = await self.estimate_fee(prepared_tx)

                tx = await prepared_tx.invoke(max_fee=int(fee * (1 + randint(15, 25) / 100)))

                for _ in range(100):
                    try:
                        receipt = await self.account.client.get_transaction_receipt(tx.hash)
                        block = receipt.block_number
                        if block:
                            return True
                    except:
                        pass
                    finally:
                        await asyncio.sleep(3)

                # if tx:
                #     logger.info(
                #         f"[{self.account.client.address_to_log}] Successfully approved {amount_to_approve} {token_name}")
                #     return True
            except Exception as err:
                if "nonce" in str(err):
                    retries += 1
                    logger.error(f"Invalid transaction nonce. Attempt {retries} of {MAX_RETRIES}. Trying to approve again.")
                    if retries == MAX_RETRIES:
                        raise ValueError("Invalid transaction nonce.")
                elif "Transaction reverted:" in str(err):
                    raise ValueError("Transaction reverted: Error in the called contract.")
                elif "balance is smaller than the transaction's max_fee" in str(err):
                    raise ValueError("Account balance is smaller than the transaction's max_fee.")
                else:
                    raise ValueError(f"Error while approving: {err}")

    async def call(self, interacted_contract_address, calldata, selector_name):
        MAX_RETRIES = 7
        retries = 0

        while retries < MAX_RETRIES:
            if retries != 0:
                    await asyncio.sleep(5)
            try:
                logger.info(f"[{self.address_to_log}] Sending tx")

                cairo_version = await self.get_cairo_version_for_txn_execution(self.account)
                print(self.address_to_log, cairo_version)

                call = Call(to_addr=interacted_contract_address, selector=get_selector_from_name(selector_name),
                            calldata=calldata)
                max_fee = TokenAmount(amount=float(uniform(0.0007534534534, 0.001)))
                response = await self.account.execute(calls=[call],
                                                      max_fee=int(max_fee.Wei * (1 + randint(15, 25) / 100)), cairo_version=cairo_version)

                for _ in range(100):
                    try:
                        receipt = await self.account.client.get_transaction_receipt(response.transaction_hash)
                        block = receipt.block_number
                        if block:
                            return True
                    except:
                        pass
                    finally:
                        await asyncio.sleep(3)

            except Exception as err:
                if "Invalid transaction nonce" in str(err):
                    retries += 1
                    logger.error(f"Invalid transaction nonce. Attempt {retries} of {MAX_RETRIES}. Trying to call again.")
                    if retries == MAX_RETRIES:
                        raise ValueError("Invalid transaction nonce.")
                elif "Transaction reverted:" in str(err):
                    raise ValueError("Transaction reverted: Error in the called contract.")
                elif "balance is smaller than the transaction's max_fee" in str(err):
                    raise ValueError("Account balance is smaller than the transaction's max_fee.")
                elif "63" in str(err):
                    retries += 1
                    logger.error(
                        f"Client failed with code 63. Attempt {retries} of {MAX_RETRIES}. Trying to call again.")
                    if retries == MAX_RETRIES:
                        raise ValueError("Client failed with code 63.")
                else:
                    raise ValueError(f"Error while sending tx: {err}")

    async def get_allowance(self, token_address, spender):
        data = ContractInfo.GetData(token_address)
        abi = data.get('abi')
        decimals = data.get('decimals')
        contract = Contract(address=token_address, abi=abi, provider=self.account)
        allowance_check = await contract.functions['allowance'].prepare(owner=self.address,
                                                                        spender=spender).call()
        if token_address == 0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3:
            amount = allowance_check.res
        else:
            amount = allowance_check.remaining
        return TokenAmount(amount=amount, decimals=decimals, wei=True)

    async def approve_interface(self, token_address, spender, decimals, amount: Optional[TokenAmount] = None):
        name = ContractInfo.GetData(token_address).get('name')
        balance = await self.get_balance(token_address=token_address, decimals=decimals)
        if balance.Wei <= 0:
            logger.error(f"[{self.address_to_log}] 0 of {name} on balance")
            return False

        if not amount or amount.Wei > balance.Wei:
            amount = balance
        approved_amount = await self.get_allowance(token_address=token_address, spender=spender)

        if approved_amount.Wei >= amount.Wei:
            logger.info(f"[{self.address_to_log}] {approved_amount.Ether} {name} approved already")
            return True

        approved_tx = await self.approve(token_address=token_address, amount_to_approve=amount.Wei, spender=spender)

        if approved_tx:
            logger.info(f"[{self.address_to_log}] Approved {amount.Ether} {name}")
            # random_sleep = randint(180, 250)
            random_sleep = randint(10, 20)
            logger.info(f"[{self.address_to_log}] Sleeping for {random_sleep} s before sending tx")
            await asyncio.sleep(random_sleep)
            return True
        return False

    async def sign_invoke_transaction(
            self,
            account: Account,
            calls: list,
            cairo_version: int,
            auto_estimate: bool = False
    ):
        try:
            return await account.sign_invoke_transaction(
                calls=calls,
                max_fee=0 if auto_estimate is False else None,
                cairo_version=cairo_version,
                auto_estimate=auto_estimate if auto_estimate is True else None
            )

        except ClientError:
            return None


    async def send_transaction(self, interacted_contract, function_name=None, **kwargs):
    #async def send_transaction(self, interacted_contract, calls, function_name=None):

        MAX_RETRIES = 4
        retries = 0

        while retries < MAX_RETRIES:
            try:
                logger.info(f"[{self.address_to_log}] Sending tx")

                cairo_version = await self.get_cairo_version_for_txn_execution(self.account)
                print(self.address_to_log, cairo_version)

                prepared_tx = interacted_contract.functions[function_name].prepare(**kwargs)
                fee = await self.estimate_fee(prepared_tx)

                tx = await prepared_tx.invoke(max_fee=int(fee * (1 + randint(15, 25) / 100)))

                # signed_invoke_transaction = await self.sign_invoke_transaction(
                #     account=self.account,
                #     calls=calls,
                #     cairo_version=cairo_version,
                #     auto_estimate=False
                # )
                # if signed_invoke_transaction is None:
                #     err_msg = "Error while signing transaction. Aborting transaction."
                #     logger.error(err_msg)


                for _ in range(100):
                    try:
                        receipt = await self.account.client.get_transaction_receipt(tx.hash)
                        block = receipt.block_number
                        if block:
                            return True
                    except:
                        pass
                    finally:
                        await asyncio.sleep(3)

            except Exception as err:
                if "nonce" in str(err):
                    retries += 1
                    logger.error(f"Invalid transaction nonce. Attempt {retries} of {MAX_RETRIES}. Trying to send tx again.")
                    if retries == MAX_RETRIES:
                        raise ValueError("Invalid transaction nonce.")
                elif "Transaction reverted:" in str(err):
                    raise ValueError("Transaction reverted: Error in the called contract.")
                elif "balance is smaller than the transaction's max_fee" in str(err):
                    raise ValueError("Account balance is smaller than the transaction's max_fee.")
                else:
                    raise ValueError(f"Error while sending tx: {err}")

    async def get_balance(self, token_address=ContractInfo.ETH.get('address'), decimals=18):
        balance = await self.account.get_balance(token_address=token_address)
        return TokenAmount(amount=balance, wei=True, decimals=decimals)

    @staticmethod
    def get_eth_price_old():
        response = requests.get(f'https://api.binance.com/api/v3/depth?limit=1&symbol=ETHUSDT')
        if response.status_code != 200:
            logger.error(f"Response Status Code: {response.status_code} json: {response.json()}")
            return
        result = response.json()
        if 'asks' not in result:
            logger.error(f"Response Status Code: {response.status_code} json: {response.json()}")
            return
        return float(result['asks'][0][0])

    @staticmethod
    def get_eth_price():
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'ethereum' in data and 'usd' in data['ethereum']:
                eth_to_usd = data['ethereum']['usd']
                return float(eth_to_usd)
        else:
            return None

    async def estimate_fee(self, tx):
        response = await tx.estimate_fee()
        overall_fee = response.overall_fee
        gas_price = response.gas_price / 10 ** 9

        while gas_price >= self.max_gwei:
            logger.info(f"Current gas price ({round(gas_price, 2)} GWEI) is higher than MAX_GWEI ({self.max_gwei} GWEI). Waiting for it to decrease...")
            await asyncio.sleep(15)
            response = await tx.estimate_fee()
            gas_price = response.gas_price / 10 ** 9

        return overall_fee

    @staticmethod
    def decode_wallet_version(version: int) -> str:
        version_bytes = version.to_bytes(31, byteorder="big")

        char_list = [chr(i) for i in version_bytes]

        version_string = "".join(char_list)

        final_version = version_string.lstrip("\x00")

        return final_version

    async def get_account_contract(self, account: Account):
        try:
            acc_abi = ContractInfo.ACCOUNT.get('abi')
            if acc_abi is None:
                return None

            return Contract(
                address=account.address,
                abi=acc_abi,
                provider=account
            )

        except ClientError:
            return None

    async def get_cairo_version_for_txn_execution(self, account: Account):
        try:
            account_contract = await self.get_account_contract(account=account)
            version = await account_contract.functions['getVersion'].call()

            version_decoded = Client.decode_wallet_version(version=version.version)

            major, minor, patch = version_decoded.split('.')

            if int(major) > 0 or int(minor) >= 3:
                return 1

            return 0

        except ClientError:
            return None

    async def account_deployed(self, account: Account):
        version = await self.get_cairo_version_for_txn_execution(account=account)
        if version is None:
            return False
        return True

    async def build_deploy_txn(self):

        nonce = await self.account.get_nonce()

        max_fee = None
        estimated_fee = True

        try:
            deploy_account_tx = await self.account.sign_deploy_account_transaction(
                class_hash=self.account.key_data.class_hash,
                contract_address_salt=self.account.key_pair.public_key,
                constructor_calldata=self.account.key_data.call_data,
                nonce=nonce,
                max_fee=max_fee,
                auto_estimate=estimated_fee
            )

            return deploy_account_tx

        except ClientError as err:
            if "unavailable for deployment" in str(err):
                err_msg = f"Account unavailable for deployment or already deployed."
                logger.error(f"[{self.address_to_log}] {err_msg}")
                raise ValueError(err)
            else:
                logger.error(f"[{self.address_to_log}] {err}")
                raise ValueError(err)

    async def wait_for_tx_receipt(
            self,
            tx_hash: int,
            time_out_sec: int
    ):
        try:
            return await self.account.client.wait_for_tx(
                tx_hash=tx_hash,
                check_interval=5,
                retries=(time_out_sec // 5) + 1
            )
        except Exception as err:
            logger.error(f"Error while waiting for txn receipt: {err}")
            raise ValueError(err)


    async def deploy(self):
        deployed = await self.account_deployed(self.account)
        logger.info(f"[{self.address_to_log}] Deployed: {deployed}")

        if not deployed:
            try:
                signed_deploy_txn = await self.build_deploy_txn()
                deploy_result = await self.account.client.deploy_account(signed_deploy_txn)
                tx_hash = deploy_result.transaction_hash

                tx_receipt = await self.wait_for_tx_receipt(tx_hash=tx_hash, time_out_sec=5)

                if tx_receipt is None:
                    logger.error(f"[{self.address_to_log}] Cant get tx receipt while deploy tx sending")

                tx_status = tx_receipt.execution_status.value if tx_receipt.execution_status is not None else None

                logger.info(f"[{self.address_to_log}] Successfully deployed! Tx status: {tx_status}, Tx hash: {hex(tx_hash)}")

            except Exception as err:
                raise ValueError(err)

        else:
            pass