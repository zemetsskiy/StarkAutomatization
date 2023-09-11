from src.config.logger import logger
from binance.client import Client


class Binance:
    @staticmethod
    def withdraw_token(api_key, api_secret, address, amount):
        try:
            client = Client(api_key, api_secret)
            response = client.withdraw(coin="ETH", address=address, amount=amount, network="ETH")
            if response:
                logger.info(f"{amount} ETH were successfully withdrawed to {address}")
                return True
        except Exception as err:
            if "User has insufficient balance" in str(err):
                logger.error(f"Insufficient balance on Binance")
                return str(err)
            else:
                logger.error(f"Error while withdrawing cash from Binance: {err}")
                return str(err)

