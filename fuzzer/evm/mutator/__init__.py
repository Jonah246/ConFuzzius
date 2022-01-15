from eth.vm.computation import BaseComputation
# from eth.vm.
from eth_utils import encode_hex, decode_hex, to_canonical_address, to_normalized_address, to_checksum_address
from .signature import GET_RESERVES, CALC_WITHDRAW_ONE_COIN, BALANCE_OF

from .attacks import *
from .types import MutatorParams

# from utils.contract import 


def log_computation_call(computation: BaseComputation):
    print('===========callTracer:')
    print('address:', to_normalized_address(computation.msg.storage_address))
    print('output:', computation.output.hex())
    print('sender', to_normalized_address(computation.msg.sender))
    print('call tracer:', computation.msg.data.hex())
    print('computation is error', computation.is_error)

def _mutate_computation(computation: BaseComputation, rate: float):
    signature = computation.msg.data[:4].hex()

    if signature == GET_RESERVES:
        mutate_get_reserves(computation, rate)
    elif signature == CALC_WITHDRAW_ONE_COIN:
        mutate_calc_withdraw_one_coin(computation, rate)
    elif signature == BALANCE_OF:
        mutate_balance_of(computation)

def _check_computation(computation: BaseComputation):
    signature = computation.msg.data[:4].hex()

    if signature == BALANCE_OF:
        mutate_balance_of(computation)
    elif signature == GET_RESERVES:
        mutate_get_reserves(computation, 1)

def mutate_computation(computation: BaseComputation, params: MutatorParams)-> None:
    to_address = to_checksum_address(computation.msg.storage_address)
    # # print('to_address', to_address, params)
    # for attack_param in params['attackRules']:
    #     if to_address == attack_param['address']:
    #         _mutate_computation(computation, attack_param['mutateRate'])
    
    _check_computation(computation)