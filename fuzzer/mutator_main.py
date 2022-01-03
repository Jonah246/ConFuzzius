import os
import sys
import random
import json

from eth.vm.computation import BaseComputation

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

from utils.traces import collect_event

from main import Fuzzer

from utils import settings
from utils.utils import initialize_logger, compile, get_interface_from_abi, get_pcs_and_jumpis, get_function_signature_mapping
from eth_utils import (
    encode_hex, decode_hex, to_canonical_address, to_normalized_address,
    big_endian_to_int, int_to_big_endian, to_hex)
from utils.control_flow_graph import ControlFlowGraph

seed = random.random()
random.seed(seed)

# solver = Solver()

class MockArgs:
    def __init__(self, source, abi, contract):
        self.source = source
        self.abi = abi
        self.contract = contract


# fork from Fuzzer
class Mutator:
    def __init__(self, tx, test_instrumented_evm: InstrumentedEVM):
        global logger

        logger = initialize_logger("Mutator  ")
        # logger.title("Mutator runs %s", tx)

        self.instrumented_evm = test_instrumented_evm

        # Initialize results
        self.results = {"errors": {}}
        self.tx = tx
        self.w3 = test_instrumented_evm.w3
        self.w3.eth.getTransactionReceipt

    def run(self) -> BaseComputation:
        from_account = to_canonical_address(decode_hex(self.tx['from']))
        self.instrumented_evm.set_vm(self.tx.blockNumber - 1)
        print(self.tx['nonce'], self.instrumented_evm.vm.state.get_nonce(from_account))
        tx = self.instrumented_evm.vm.create_unsigned_transaction(
            nonce=self.tx['nonce'],
            gas_price=self.tx['gasPrice'],
            gas=self.tx['gas'],
            to=to_canonical_address(self.tx['to']),
            value=self.tx['value'],
            data=decode_hex(self.tx['input'])
        )
        tx = SpoofTransaction(tx, from_=from_account)
        BLOCK_ID = self.tx.blockNumber - 1
        return self.instrumented_evm.execute(tx, False)



instrumented_evm = InstrumentedEVM(settings.RPC_HOST, settings.RPC_PORT)
instrumented_evm.set_vm_by_name(settings.EVM_VERSION)
tx_hash = '0xa07d381e9f1ebe49c26735118798449f35975e0baa2bd174a7e3c976583b7e61'

tx = instrumented_evm.w3.eth.getTransaction(tx_hash)
mutator = Mutator(tx, instrumented_evm)
result = mutator.run()
# print('type', type(result), result.output, result.is_success)
# print(type(result.trace))
import json
# List[Tuple[Address, Tuple[int, ...], bytes]]
logs = result.get_log_entries()
# print(result.trace)
print(collect_event(mutator.w3.codec, logs))
