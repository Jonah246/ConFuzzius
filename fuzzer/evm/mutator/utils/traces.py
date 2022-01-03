import json
from hexbytes import HexBytes
from web3._utils.events import get_event_data
from utils.utils import w3


def convert_event(event):
    topics = []
    if 'topics' in event.keys():
        for topic in event['topics']:
            topics.append(HexBytes(topic))
        event['topics'] = topics
    if 'data' in event.keys():
        event['data'] = HexBytes(event['data'])
    
    # we dont need these fileds; we just insert useless
    event['blockNumber'] = 0
    event['transactionIndex'] = 0
    event['blockHash'] = HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')
    event['transactionHash'] = HexBytes('0x0000000000000000000000000000000000000000000000000000000000000000')
    return event


def collect_event(events, event_type='transfer'):
    erc20_transfer_abi = json.loads('{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"}')
    decoded_events = []

    if event_type == 'transfer':
        for event in events:
            try:
                decoded_events.append(get_event_data(w3.codec, erc20_transfer_abi, convert_event(event)))
            except Exception as e:
                # print(e)
                pass
    else:
        raise "unsupported"
    return decoded_events

