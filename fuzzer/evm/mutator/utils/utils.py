import web3
from web3 import Web3
import json
import os

# base_path = os.environ["AUDIT_BASE_PATH"]
base_path = ""
w3 = Web3(Web3.HTTPProvider('http://localhost:8545', request_kwargs={'timeout': 600}))
# from web3.middleware import geth_poa_middleware
# w3.middleware_onion.inject(geth_poa_middleware, layer=0)
# w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/HjJCFn7WgkefSa5VevGZz2Af_GrjOiZS'))
def create_contract(abi_path, address):
    with open(abi_path, 'r') as f:
        abi = f.read()
        f.close()
    abi = json.loads(abi)
    contract = w3.eth.contract(abi=abi, address=address)
    return contract

def deploy_contract(builds, *args):
    contract = w3.eth.contract(abi=builds['abi'], bytecode=builds['bytecode'])
    tx_hash = contract.constructor(*args).transact({'from': w3.eth.accounts[0]})
    receipt = w3.eth.getTransactionReceipt(tx_hash)
    return w3.eth.contract(abi=builds['abi'], address=receipt['contractAddress'])

def deploy_contract(builds, *args):
    bytecode = builds['bytecode']
    try:
        contract = w3.eth.contract(abi=builds['abi'], bytecode=bytecode)
    except Exception as e:
        print(builds['linkReferences'])
        raise e
    tx_hash = contract.constructor(*args).transact({'from': w3.eth.accounts[0], 'gas': 12450000})
    receipt = w3.eth.getTransactionReceipt(tx_hash)
    return w3.eth.contract(abi=builds['abi'], address=receipt['contractAddress'])

def open_build(contract_name, prefix = '', file_name=''):
    if file_name == '':
        file_name = contract_name
    cur_base = os.path.join(base_path, prefix)
    f = open(os.path.join(
        cur_base, '{}.sol/{}.json'.format(file_name, contract_name)))
    data = json.loads(f.read())
    f.close()
    return data

def deploy_contract_with_lib(builds, lib_ref, *args):
    bytecode = insert_lib_adr(builds, lib_ref)
    try:
        contract = w3.eth.contract(abi=builds['abi'], bytecode=bytecode)
    except Exception as e:
        print(builds['linkReferences'])
        raise e
    tx_hash = contract.constructor(*args).transact({'from': w3.eth.accounts[0], 'gas': 12450000})
    receipt = w3.eth.getTransactionReceipt(tx_hash)
    return w3.eth.contract(abi=builds['abi'], address=receipt['contractAddress'])

def insert_lib_adr(build, lib_addrs):
    ref = build['linkReferences']
    bytecode = build['bytecode']
    prefix = 2 # '0x'
    lib_list = {}
    for _, data in ref.items():
        for library, locations in data.items():
            locations = locations[0]
            start_index = prefix + int(locations['start']) * 2
            end_index = start_index + int(locations['length']) * 2
            lib_list[library] = bytecode[start_index: end_index]
    
    for lib, address in lib_addrs.items():
        bytecode = bytecode.replace(lib_list[lib], address[2:])
    return bytecode
