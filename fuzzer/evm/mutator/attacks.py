from eth.vm.computation import BaseComputation
from eth_utils import encode_hex, decode_hex, to_canonical_address, to_normalized_address, to_checksum_address

from .contracts.uniswap import PAIR_ABI

from .utils.utils import w3

from eth_abi import (
    decode_abi,
    encode_abi,
)


def get_abi_output_types(abi):
    if abi['type'] == 'fallback':
        return []
    else:
        return [arg['type'] for arg in abi['outputs']]

def mutate_calc_withdraw_one_coin(computation: BaseComputation, rate: float) -> None:
    output_type = ['uint256']
    
    return_value = decode_abi(output_type, computation.output)[0]
    mutated_value = int(return_value * rate)
    computation.output = encode_abi(output_type, [mutated_value])

def mutate_balance_of(computation: BaseComputation) -> None:
    output_type = ['uint256']

    return_value = decode_abi(output_type, computation.output)[0]
    address = decode_abi(["address"], decode_hex(
        computation.msg.data[4:].hex()))
    to_address = to_checksum_address(computation.msg.storage_address)
    print('contract: {}, adr: {}, value: {}'.format(to_address, address, return_value))


def mutate_get_reserves(computation: BaseComputation, rate: float) -> None:
    pair = w3.eth.contract(abi=PAIR_ABI)
    # output_type = get_abi_output_types(pair.find_functions_by_name('getReserves')[0].abi)
    output_type = ['uint112', 'uint112', 'uint32']

    to_address = to_checksum_address(computation.msg.storage_address)


    reserve_a, reserve_b, last_update_time = decode_abi(
        output_type, computation.output)

    print('contract: {}, , time: {}, reserve a: {}, reserve b: {}'.format(
        to_address, last_update_time, reserve_a, reserve_b))
    reserve_a = int(reserve_a * rate)
    reserve_b = int(reserve_b // rate)
    computation.output = encode_abi(output_type, (reserve_a, reserve_b, last_update_time))
