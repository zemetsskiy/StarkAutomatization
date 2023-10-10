import random
import string
from dataclasses import dataclass

from src.utils.Info import ContractInfo
from src.utils.Client import Client
from src.config.logger import logger
from starknet_py.contract import Contract


@dataclass
class DataForDmail:
    entities = ['Humans', 'Animals', 'Stars', 'Planets', 'Machines', 'Ideas', 'Dreams', 'Feelings', 'Stories',
                'Songs', 'Foods', 'Places', 'moments', 'Moments', 'Artworks', 'Inventions', 'Cultures', 'Traditions',
                'Languages', 'Games', 'Theories', 'Buildings', 'Computers', 'Philosophies', 'Books', 'Events',
                'Rituals', 'Religions', 'Movements', 'Discoveries', 'Technologies', 'Medicines', 'Concepts',
                'Laws', 'Mysteries', 'Beliefs', 'Systems', 'Teams', 'Groups', 'Communities']

    actions = ['move', 'shine', 'grow', 'connect', 'inspire', 'fade', 'change', 'merge', 'express', 'challenge',
               'transform', 'resonate', 'collide', 'emerge', 'disappear', 'influence', 'reflect', 'capture',
               'combine', 'contrast', 'defend', 'attack', 'adapt', 'learn', 'teach', 'question', 'answer', 'react',
               'adjust', 'compete', 'cooperate', 'integrate', 'isolate', 'progress', 'decline', 'innovate', 'imitate']

    things = ['lights', 'sounds', 'flavors', 'emotions', 'paths', 'rhythms', 'patterns', 'colors', 'words',
              'memories', 'challenges', 'visions', 'voices', 'echoes', 'shapes', 'textures', 'details',
              'perspectives', 'fragments', 'vibrations', 'theories', 'principles', 'elements', 'ingredients',
              'materials', 'tools', 'mechanisms', 'structures', 'protocols', 'strategies', 'procedures', 'methods',
              'formulas', 'recipes', 'guidelines', 'criteria', 'standards', 'metrics', 'indices']


class Dmail:
    DMAIL_CONTRACT_ADDRESS = ContractInfo.DMAIL.get('address')
    DMAIL_ABI = ContractInfo.DMAIL.get('abi')

    def __init__(self, client: Client):
        self.client = client
        self.contract = Contract(address=Dmail.DMAIL_CONTRACT_ADDRESS, abi=Dmail.DMAIL_ABI, provider=self.client.account)

    async def send_message(self):
        try:
            logger.info(f"[{self.client.address_to_log}] Sending message [Dmail]")
            email = self.get_random_email()
            text = self.construct_random_sentence()
            tx_hash = await self.client.send_transaction(interacted_contract=self.contract,
                                                         function_name='transaction',
                                                         #calls=[email, text]
                                                         to=email,
                                                         theme=text)
            if tx_hash:
                logger.info(f"[{self.client.address_to_log}] Message '{text}' was successfully sent to {email} [Dmail]")
                return True
        except Exception as err:
            if "Contract not found" in str(err):
                logger.error(f"[{self.client.address_to_log}] Seems contract (address) is not deployed yet because it did not have any txs before [Dmail]")
            elif "nonce" in str(err):
                raise ValueError(str(err))
            elif "Cannot connect to host" in str(err):
                raise ValueError("Some problems with rpc. Cannot connect to host starknet-mainnet.infura.io [Dmail]")
            elif "Transaction reverted: Error in the called contract." in str(err):
                raise ValueError(str(err))
            else:
                logger.error(f"[{self.client.address_to_log}] Error while sending message: {err} [Dmail]")

    @staticmethod
    def get_random_email():
        domains = ['@gmx.com', '@gmail.com', '@dmail.ai']

        symbols = list(string.ascii_letters + string.digits)
        mail_length = random.randint(5, 15)

        mail = ''.join(random.choice(symbols) for _ in range(mail_length))
        mail += random.choice(domains)
        return mail

    @staticmethod
    def construct_random_sentence():
        MAX_LENGTH = 31
        all_elements = DataForDmail.entities + DataForDmail.actions + DataForDmail.things
        sentence = ' '.join(random.sample(all_elements, random.randint(1, 4))).lower()

        if len(sentence) > MAX_LENGTH:
            sentence = sentence[:MAX_LENGTH]

        return sentence