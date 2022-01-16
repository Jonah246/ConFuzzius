import json
from hexbytes import HexBytes
from web3._utils.events import get_event_data
from eth_abi.codec import (
    ABICodec,
)
from web3 import Web3
import re

from web3.types import (
    ABIEvent,
    ABIEventParams,
    EventData,
    LogReceipt,
)

from eth_utils import (
    to_checksum_address, int_to_big_endian
)

from typing import (  # noqa: F401
    Any,
    Callable,
    cast,
    Dict,
    List,
    Tuple,
    Union,
)


def pact_to_byte32(data: bytes) -> HexBytes:
    if len(data) < 32:
        return HexBytes(bytes(32 - len(data)) + data)
    return HexBytes(data)

def stack_item_to_hex(item):
    if item[0] == bytes:
        return pact_to_byte32(item[1]).hex()[2:]
    else:
        return pact_to_byte32(HexBytes(int_to_big_endian(item[1]))).hex()[2:]

def trace_to_json(trace: List):
    serializable_list = []
   
    for step in trace:
        if 'stack' in step.keys():
            stacks = [] 
            for item in step['stack']:
                stacks.append(stack_item_to_hex(item))
            step['stack'] = stacks
            serializable_list.append(step)
    return json.dumps(serializable_list)



def convert_event(log: Tuple[bytes, Tuple[int, ...], bytes]) -> LogReceipt:
    address, topics, data = log
    topics = [pact_to_byte32(HexBytes(int_to_big_endian(topic))) for topic in topics]
    log_receipt =  LogReceipt(
        address= to_checksum_address(address),
        blockHash=HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000'),
        transactionHash=HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000'),
        transactionIndex=0,
        topic=topics[0],
        topics=topics,
        data=data,
        logIndex=0,
        blockNumber=0,
        )
    return log_receipt

def get_revert_reason(output: bytes):
    shrimp_output = output[68:]
    if len(shrimp_output) % 2 != 0:
        shrimp_output = shrimp_output + bytes(0)
    try:
        msg = Web3.toText(shrimp_output)
        return msg
    except Exception as e:
        print(e)
        return output

def collect_event(codec: ABICodec, logs: Tuple[Tuple[bytes, Tuple[int, ...], bytes], ...], event_type='transfer'):
    erc20_transfer_abi = json.loads('{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"}')
    decoded_events = []

    if event_type == 'transfer':
        for log in logs:
            try:
                decoded_events.append(get_event_data(codec, erc20_transfer_abi, convert_event(log)))
            except Exception as e:
                pass
    else:
        raise "unsupported"
    return decoded_events

