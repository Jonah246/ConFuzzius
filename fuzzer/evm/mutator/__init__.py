from eth.vm.computation import BaseComputation
# from eth.vm.
from eth_utils import encode_hex, decode_hex, to_canonical_address, to_normalized_address
from .signature import GET_RESERVES, CALC_WITHDRAW_ONE_COIN

from .attacks import *

# from utils.contract import 


def log_computation_call(computation: BaseComputation):
    print('===========callTracer:')
    print('address:', to_normalized_address(computation.msg.storage_address))
    print('output:', computation.output.hex())
    print('sender', to_normalized_address(computation.msg.sender))
    print('call tracer:', computation.msg.data.hex())
    print('computation is error', computation.is_error)

def mutate_computation(computation: BaseComputation)-> None:
    signature = computation.msg.data[:4].hex()

    if signature == GET_RESERVES:
        mutate_get_reserves(computation, 1)
    elif signature == CALC_WITHDRAW_ONE_COIN:
        mutate_calc_withdraw_one_coin(computation, 1.1)
    