import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()

ABIS_DIR = os.path.join(os.path.join(ROOT_DIR), 'abis')

ERC20_ABI_PATH = os.path.join(ABIS_DIR, 'erc20.json')
DAI_ABI_PATH = os.path.join(ABIS_DIR, 'dai.json')

JEDISWAP_ABI_PATH = os.path.join(ABIS_DIR, 'jediswap.json')
AVNUFI_ABI_PATH = os.path.join(ABIS_DIR, 'avnufi.json')
DMAIL_ABI_PATH = os.path.join(ABIS_DIR, 'dmail.json')
STARKNETID_ABI_PATH = os.path.join(ABIS_DIR, 'starknetid.json')
TENKSWAP_ABI_PATH = os.path.join(ABIS_DIR, '10kswap.json')

JEDISWAP_ETHUSDC_ABI_PATH = os.path.join(ABIS_DIR, 'jediswap_ethusdc.json')
JEDISWAP_ETHUSDT_ABI_PATH = os.path.join(ABIS_DIR, 'jediswap_ethusdt.json')
JEDISWAP_USDCUSDT_ABI_PATH = os.path.join(ABIS_DIR, 'jediswap_usdcusdt.json')

STARKVERSE_ABI_PATH = os.path.join(ABIS_DIR, 'starkverse.json')
STARKNETIDNFT_ABI_PATH = os.path.join(ABIS_DIR, 'starknetidnft.json')
BRIDGE_ABI_PATH = os.path.join(ABIS_DIR, 'bridge.json')