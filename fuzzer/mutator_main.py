import os
import sys
import random
import json

from eth.vm.computation import BaseComputation
from typing import Union, Optional
from eth_typing import (
    Address,
    BlockNumber,
    ChecksumAddress,
    Hash32,
    HexStr,
    # TxData
)
from web3.types import TxData, BlockData
from z3.z3 import Bool

# from z3 import Solver

from evm import InstrumentedEVM
from engine import EvolutionaryFuzzingEngine
from engine.components import Generator, Individual, Population

from engine.environment import FuzzingEnvironment
from engine.analysis import SymbolicTaintAnalyzer
from engine.analysis import ExecutionTraceAnalyzer
from detectors import DetectorExecutor
from eth.vm.spoof import SpoofTransaction
from evm.storage_emulation import BLOCK_ID

from utils.traces import collect_event, get_revert_reason

from evm.mutator.types import MutatorParams, AttackParams
from evm.block import get_header_fromblock_data
from evm.transaction import build_transaction_from_transaction_data

from main import Fuzzer

from utils import settings
from utils.utils import initialize_logger, compile, get_interface_from_abi, get_pcs_and_jumpis, get_function_signature_mapping
from eth_utils import (
    encode_hex, decode_hex, to_canonical_address, to_normalized_address,
    big_endian_to_int, int_to_big_endian, to_hex)
from utils.control_flow_graph import ControlFlowGraph

seed = random.random()
random.seed(seed)

def detection_compare_revert_and_transfers(normal_transfers, transfers):

    if len(transfers) != len(normal_transfers):
        return {
            'type': 'different_transfers',
            'msg': 'normal traces has {} transfers; mutated traces has {} transfers'.format(
            len(normal_transfers), len(transfers))
        }

    inconsists = []
    
    for i in range(len(normal_transfers)):
        normal = normal_transfers[i]
        mutated = transfers[i]

        if normal['address'] != mutated['address']:
            inconsists.append('source address inconsists at log Index: {}\n normal: {}, mutated: {}'.format(
                i, normal['address'], mutated['address']))
            continue

        if normal['args']['from'] != mutated['args']['from']:
            inconsists.append('from address inconsists at log Index: {}\n normal: {}, mutated: {}'.format(
                i, normal['args']['from'], mutated['args']['from']))
        
        if normal['args']['to'] != mutated['args']['to']:
            inconsists.append('to address inconsists at log Index: {}\n normal: {}, mutated: {}'.format(
                i, normal['args']['to'], mutated['args']['to']))
        
        if normal['args']['value'] != mutated['args']['value']:
            inconsists.append('Transfer value inconsists at log Index: {}\n normal: {}, mutated: {}'.format(
                i, normal['args']['value'], mutated['args']['value'])) 
    if len(inconsists) == 0:
        return {}

    return {
        'type': 'value-inconsists',
        'msg': json.dumps(inconsists),
    }


class MockArgs:
    def __init__(self, source, abi, contract):
        self.source = source
        self.abi = abi
        self.contract = contract


# fork from Fuzzer
class Mutator:
    def __init__(self, test_instrumented_evm: InstrumentedEVM):
        global logger

        logger = initialize_logger("Mutator  ")
        # logger.title("Mutator runs %s", tx)

        self.instrumented_evm = test_instrumented_evm

        # Initialize results
        self.results = {"errors": {}}
        self.w3 = test_instrumented_evm.w3
    
    def set_params(self, mutatorParams: MutatorParams):
        self.instrumented_evm.set_mutator_params(mutatorParams)


    """
        run_tx executes trace_trasaction in the instrumented_evm
        @params: params: MutatorParams indicates the rules for mutator to mutate
        @params: discatd_state_change: whether to disard the state change of the current transacion.
    """
    def run_tx(
        self, tx_hash: Union[HexStr, Hash32],
        params: Optional[MutatorParams] = None,
        discard_state_change: Optional[Bool] = True) -> BaseComputation:
        if params:
            self.set_params(params)
        tx = self.w3.eth.get_transaction(tx_hash)

        from_account = to_canonical_address(tx['from'])
        
        if hasattr(self.instrumented_evm.vm, 'new_unsigned_access_list_transaction'):
            print("support!!")
        base_unsigned_tx = self.instrumented_evm.vm.create_unsigned_transaction(
            **tx
        )
        BLOCK_ID = tx.blockNumber

        self.instrumented_evm.set_vm(BLOCK_ID)
        self.instrumented_evm.restore_from_snapshot()
        spoof_tx = SpoofTransaction(base_unsigned_tx, from_=from_account)

        result = self.instrumented_evm.execute(
            spoof_tx,
            debug=False)
        return result

    def run_raw_tx(self, tx: TxData, block: BlockData) -> BaseComputation:
        from_account = to_canonical_address(tx['from'])
        
        base_unsigned_tx = self.instrumented_evm.vm.create_unsigned_transaction(
            nonce=tx['nonce'],
            gas_price=tx['gasPrice'],
            gas=tx['gas'],
            to=to_canonical_address(tx['to']),
            value=tx['value'],
            data=decode_hex(tx['input']),
        )
        # self.instrumented_evm.create_snapshot()
        result = self.instrumented_evm.apply_transaction(
            get_header_fromblock_data(block),
            build_transaction_from_transaction_data(self.instrumented_evm.vm, tx))
        return result

    def trace_block(
        self, block_number: BlockNumber
    ):
        block = self.w3.eth.get_block(block_number)
        BLOCK_ID = block_number - 1
        self.instrumented_evm.set_vm(BLOCK_ID)
        txs = block['transactions']
        for tx_hash in txs[:1]:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            print('receipt status:', receipt['status'], tx_hash.hex())

            result = self.run_raw_tx(tx, block)
            print(result.is_success, receipt['status'])

            if result.is_error and receipt['status'] == 1:
                print(tx['type'])
                print(result._error)
                print('revert', get_revert_reason(result.output))




instrumented_evm = InstrumentedEVM(settings.RPC_HOST, settings.RPC_PORT)
instrumented_evm.set_vm_by_name(settings.EVM_VERSION)
# instrumented_evm.set_vm_by_name()
instrumented_evm.create_snapshot()

# tx_hash = '0xa07d381e9f1ebe49c26735118798449f35975e0baa2bd174a7e3c976583b7e61'
tx_hash = '0x40967af3e2db0f16ca84c55807cdad2adca03cc07ae5b06e5e61b63ddb2b768c'

tx = instrumented_evm.w3.eth.getTransaction(tx_hash)

mutator_params = MutatorParams(
        attackRules=[
            AttackParams(
                address="0xb6c057591E073249F2D9D88Ba59a46CFC9B59EdB"
                ,mutateRate=0.5)
])
mutator = Mutator(instrumented_evm,)

mutator.trace_block(13964000)
# result = mutator.run_tx(tx_hash, mutator_params)

# if not result.is_success:
#     print('revert', get_revert_reason(result.output))
# logs = result.get_log_entries()
# pre_events = collect_event(mutator.w3.codec, logs)

# mutator_params = MutatorParams(
#         attackRules=[
#             AttackParams(
#                 address="0xb6c057591E073249F2D9D88Ba59a46CFC9B59EdB"
#                 ,mutateRate=0.9)
# ])

# result = mutator.run_tx(tx_hash, mutator_params)
# if not result.is_success:
#     print('revert', get_revert_reason(result.output))
# logs = result.get_log_entries()
# post_events = collect_event(mutator.w3.codec, logs)

# print(detection_compare_revert_and_transfers(post_events, pre_events))


