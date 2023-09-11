import ccxt
import requests

from src.config.logger import logger

APIKEY = "8706d947-7096-41bc-a726-0e68ad6c41b9"
APISECRET = "A3FAA4965EE1F86E72B00ED77E3CF2E0"
PASS = "Yaroslav=>482228"
BASE_URL = 'https://aws.okex.com'
PROXY_FOR_OKX = None

class Okx:
    BASE_URL = "https://www.okcoin.com"  # Используйте правильный базовый URL

    @staticmethod
    def get_server_time():
        response = requests.get(f"{Okx.BASE_URL}/api/v5/public/time")
        data = response.json()
        if data and data.get("code") == "0":
            return data["data"][0]["ts"]
        else:
            raise Exception("Failed to fetch server time from Okcoin")

    @staticmethod
    def withdraw(wallet, amount):
        try:
            logger.info(f"[{wallet}] Withdrawing to: {wallet}")

            server_time = Okx.get_server_time()

            params = {
                'apiKey': APIKEY,
                'secret': APISECRET,
                'password': PASS,
                'enableRateLimit': True,
                'headers': {
                    'expTime': server_time  # Устанавливаем expTime в заголовке запроса
                }
            }

            if PROXY_FOR_OKX:
                params['proxies'] = PROXY_FOR_OKX

            exchange = ccxt.okx(params)
            withdraw = exchange.withdraw('ETH', amount, wallet,
                                         params={
                                             "toAddress": wallet,
                                             "chainName": 'ERC20',
                                             "dest": 4,
                                             "pwd": '-',
                                             "amt": amount,
                                             "network": 'ERC20'
                                         })

            if withdraw.get('info'):
                logger.info(f"[{wallet}] Withdrawed {amount} ETH")
                return True

        except Exception as err:
            logger.error(f"[{wallet}] Couldn't withdraw ETH | {err}")
