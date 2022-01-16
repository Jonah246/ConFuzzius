from typing import Optional, Set, cast
from copy import deepcopy
from eth.vm.computation import BaseComputation
from eth._utils.address import force_bytes_to_address
from eth_utils import to_bytes, to_normalized_address, to_hex, big_endian_to_int, int_to_big_endian


from utils import settings
from utils.traces import stack_item_to_hex

from eth.vm.logic.invalid import (
    InvalidOpcode,
)
from eth.exceptions import (
    Halt,
    VMError,
)

from .mutator import mutate_computation, log_computation_call



def fuzz_call_opcode_fn(computation, opcode_fn) -> None:
    gas = computation.stack_pop1_int()
    to = computation.stack_pop1_bytes()
    _to = to_normalized_address(to_hex(force_bytes_to_address(to)))
    if settings.ENVIRONMENTAL_INSTRUMENTATION and hasattr(computation.state, "fuzzed_call_return") and computation.state.fuzzed_call_return is not None\
            and _to in computation.state.fuzzed_call_return and computation.state.fuzzed_call_return[_to] is not None:
        (
            value,
            memory_input_start_position,
            memory_input_size,
            memory_output_start_position,
            memory_output_size,
        ) = computation.stack_pop_ints(5)
        computation.stack_push_int(computation.state.fuzzed_call_return[_to])
    else:
        computation.stack_push_bytes(to)
        computation.stack_push_int(gas)
        opcode_fn(computation=computation)
    return _to


def fuzz_extcodesize_opcode_fn(computation, opcode_fn) -> None:
    to = computation.stack_pop1_bytes()
    _to = to_normalized_address(to_hex(force_bytes_to_address(to)))
    if settings.ENVIRONMENTAL_INSTRUMENTATION and hasattr(computation.state, "fuzzed_extcodesize") and computation.state.fuzzed_extcodesize is not None\
            and _to in computation.state.fuzzed_extcodesize and computation.state.fuzzed_extcodesize[_to] is not None:
        computation.stack_push_int(computation.state.fuzzed_extcodesize[_to])
    else:
        computation.stack_push_bytes(to)
        opcode_fn(computation=computation)


def fuzz_returndatasize_opcode_fn(previous_call_address, computation, opcode_fn) -> None:
    opcode_fn(computation=computation)
    size = computation.stack_pop1_int()
    if settings.ENVIRONMENTAL_INSTRUMENTATION and hasattr(computation.state, "fuzzed_returndatasize") and computation.state.fuzzed_returndatasize is not None\
            and previous_call_address in computation.state.fuzzed_returndatasize and computation.state.fuzzed_returndatasize[previous_call_address] is not None:
        computation.stack_push_int(
            computation.state.fuzzed_returndatasize[previous_call_address])
    else:
        computation.stack_push_int(size)


def fuzz_balance_opcode_fn(computation, opcode_fn) -> None:
    if settings.ENVIRONMENTAL_INSTRUMENTATION and hasattr(computation.state, "fuzzed_balance") and computation.state.fuzzed_balance is not None:
        computation.stack_pop1_bytes()
        computation.stack_push_int(computation.state.fuzzed_balance)
    else:
        opcode_fn(computation=computation)


def fuzz_apply_mutator(computation) -> None:
    # is it a good way to pollute computation state
    if hasattr(computation.state, "mutator_params"):
        mutate_computation(computation, computation.state.mutator_params)
    else:
        mutate_computation(computation, None)

def timestamp_opcode_fn(computation) -> None:
    if settings.ENVIRONMENTAL_INSTRUMENTATION and hasattr(computation.state, "fuzzed_timestamp") and computation.state.fuzzed_timestamp is not None:
        computation.stack_push_int(computation.state.fuzzed_timestamp)
    else:
        computation.stack_push_int(computation.state.timestamp)


def blocknumber_opcode_fn(computation) -> None:
    if settings.ENVIRONMENTAL_INSTRUMENTATION and hasattr(computation.state, "fuzzed_blocknumber") and computation.state.fuzzed_blocknumber is not None:
        computation.stack_push_int(computation.state.fuzzed_blocknumber)
    else:
        computation.stack_push_int(computation.state.block_number)

def sort_storage_trace(storage):
    return dict(sorted(storage.items(), key=lambda item: item[1]))

def trace_load_storage(computation: BaseComputation, slot):
    # storage_trace[slot] = value
    value = stack_item_to_hex(computation._stack.values[-1])
    computation.storage_trace[slot] = value

def trace_set_storage(computation: BaseComputation):
    # storage_trace[slot] = value
    slot = stack_item_to_hex(computation._stack.values[-1])
    value = stack_item_to_hex(computation._stack.values[-2])
    computation.storage_trace[slot] = value
    # print('trace set', stack_item_to_hex(slot), stack_item_to_hex(value))


@classmethod
def fuzz_apply_computation(cls, state, message, transaction_context):

    with cls(state, message, transaction_context) as computation:

        # Early exit on pre-compiles
        from eth.vm.computation import NO_RESULT
        precompile = computation.precompiles.get(
            message.code_address, NO_RESULT)
        if precompile is not NO_RESULT:
            precompile(computation)
            return computation
        show_debug2 = computation.logger.show_debug2

        computation.trace = list()
        computation.storage_trace = dict()
        if hasattr(state, 'trace'):
            computation.trace = state.trace


        previous_stack = []
        opcode_lookup = computation.opcodes
        for opcode in computation.code:
            try:
                opcode_fn = opcode_lookup[opcode]
            except KeyError:
                opcode_fn = InvalidOpcode(opcode)

            if show_debug2:
                # We dig into some internals for debug logs
                base_comp = cast(BaseComputation, computation)
                computation.logger.debug2(
                    "OPCODE: 0x%x (%s) | pc: %s | stack: %s",
                    opcode,
                    opcode_fn.mnemonic,
                    max(0, computation.code.program_counter - 1),
                    base_comp._stack,
                )

            memory = None
            previous_pc = computation.code.program_counter
            previous_gas = computation.get_gas_remaining()
            computation.trace.append(
                {
                    "pc": max(0, previous_pc - 1),
                    "op": opcode_fn.mnemonic,
                    "depth": computation.msg.depth + 1,
                    # "error": deepcopy(computation._error),
                    "stack": previous_stack,
                    # "memory": memory,
                    "gas": computation.get_gas_remaining(),
                    "storage": sort_storage_trace(computation.storage_trace)
                    # "gas_used_by_opcode": previous_gas - computation.get_gas_remaining()
                })
            try:

                if opcode == 0x42:  # TIMESTAMP
                    opcode_fn(computation=computation)
                    # timestamp_opcode_fn(computation=computation)
                elif opcode == 0x43:  # NUMBER
                    opcode_fn(computation=computation)
                    # blocknumber_opcode_fn(computation=computation)
                elif opcode == 0x54:  # SLOAD
                    slot = stack_item_to_hex(computation._stack.values[-1])
                    opcode_fn(computation=computation)
                    trace_load_storage(computation, slot)
                elif opcode == 0x55:  # SSTORE
                    trace_set_storage(computation)
                    opcode_fn(computation=computation)
                else:
                # elif opcode == 0x31:  # BALANCE
                #     fuzz_balance_opcode_fn(computation=computation, opcode_fn=opcode_fn)
                # elif opcode == 0xf1: # CALL
                #     previous_call_address = fuzz_call_opcode_fn(computation=computation, opcode_fn=opcode_fn)
                # elif opcode == 0x3b: # EXTCODESIZE
                #     fuzz_extcodesize_opcode_fn(computation=computation, opcode_fn=opcode_fn)
                # elif opcode == 0x3d: # RETURNDATASIZE
                #     fuzz_returndatasize_opcode_fn(previous_call_address, computation=computation, opcode_fn=opcode_fn)
                # elif opcode == 0x20: # SHA3
                #     start_position, size = computation.stack_pop_ints(2)
                #     memory = computation.memory_read_bytes(start_position, size)
                #     computation.stack_push_int(size)
                #     computation.stack_push_int(start_position)
                #     opcode_fn(computation=computation)
                # else:
                    opcode_fn(computation=computation)
            except Halt:
                fuzz_apply_mutator(computation)
                break

            finally:
                # computation.trace.append(
                #     {
                #         "pc": max(0, previous_pc - 1),
                #         "op": opcode_fn.mnemonic,
                #         "depth": computation.msg.depth + 1,
                #         # "error": deepcopy(computation._error),
                #         "stack": previous_stack,
                #         # "memory": memory,
                #         "gas": computation.get_gas_remaining(),
                #         "gas_used_by_opcode": previous_gas - computation.get_gas_remaining()
                #     }
                # )
                previous_stack = list(computation._stack.values)

        state.trace = computation.trace
    return computation


def record_logs(computation: BaseComputation, log_size: int) -> BaseComputation:
    start_position, size = computation.stack_pop_ints(2)
    topics = []
    for i in range(log_size):
        topic = computation.stack_pop1_any()
        topics.append(topic)
    hex_topics = []
    for topic in topics[::-1]:
        if type(topic) is int:
            hex_topics.append(to_hex(topic))
            computation.stack_push_int(topic)
        else:
            hex_topics.append(topic.hex())
            computation.stack_push_bytes(topic)

    computation.stack_push_int(size)
    computation.stack_push_int(start_position)

    computation.events.append({
        'address': to_normalized_address(computation.msg.storage_address),
        'data': to_hex(computation.memory_read_bytes(start_position, size)),
        'logIndex': len(computation.events),
        'topcis': hex_topics[::-1],
    })
    return computation
