from typing import cast, Dict

from eth.abc import VirtualMachineAPI, SignedTransactionAPI, BlockAPI
from eth.vm.spoof import SpoofTransaction
from eth_utils import to_canonical_address, decode_hex
from eth.tools._utils.normalization import normalize_signed_transaction
from eth_keys.datatypes import PrivateKey


from web3.types import TxData
def build_transaction_from_transaction_data(vm: VirtualMachineAPI, tx_data: TxData) -> SignedTransactionAPI:
    # print(**tx_data)
    from_account = to_canonical_address(tx_data['from'])
    # unsigned_tx = {}
    if tx_data.type == '0x0': 
        unsigned_tx = vm.get_transaction_builder().create_unsigned_transaction(
            nonce=tx_data['nonce'],
            gas_price=tx_data['gasPrice'],
            gas=tx_data['gas'],
            to=to_canonical_address(tx_data['to']),
            value=tx_data['value'],
            data=decode_hex(tx_data['input']),
        )
    elif tx_data.type == '0x1':
        unsigned_tx = vm.get_transaction_builder().new_unsigned_access_list_transaction(
            chain_id=int(tx_data['chainId'], 0),
            nonce=tx_data['nonce'],
            gas_price=tx_data['gasPrice'],
            gas=tx_data['gas'],
            to=to_canonical_address(tx_data['to']),
            value=tx_data['value'],
            data=decode_hex(tx_data['input']),
            access_list=tx_data['accessList']
        )
    elif tx_data.type == '0x2':
        unsigned_tx = vm.get_transaction_builder().new_unsigned_dynamic_fee_transaction(
            chain_id=int(tx_data['chainId'], 0),
            nonce=tx_data['nonce'],
            max_priority_fee_per_gas=tx_data['maxPriorityFeePerGas'],
            max_fee_per_gas=tx_data['maxFeePerGas'],
            gas=tx_data['gas'],
            to=to_canonical_address(tx_data['to']),
            value=tx_data['value'],
            data=decode_hex(tx_data['input']),
            access_list=tx_data['accessList']
        )
    else:
        raise Exception("undefined transaction type")


    return SpoofTransaction(unsigned_tx, from_=from_account)
