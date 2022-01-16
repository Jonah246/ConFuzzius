
from eth_utils import to_canonical_address, decode_hex, encode_hex
from eth.vm.forks.london.headers import LondonBlockHeader
from eth.rlp.headers import BlockHeader
from eth.abc import BlockHeaderAPI
from web3.types import TxData, BlockData

def get_header_fromblock_data(block: BlockData) -> BlockHeaderAPI:
    if hasattr(block, 'baseFeePerGas'):
        block_header = LondonBlockHeader(difficulty=block.difficulty,
                                            block_number=block.number,
                                            gas_limit=block.gasLimit,
                                            timestamp=block.timestamp,
                                            coinbase=to_canonical_address(
                                                block.miner),  # default value
                                            parent_hash=block.parentHash,
                                            uncles_hash=block.uncles,
                                            state_root=block.stateRoot,
                                            # state_root = parentblock.stateRoot,
                                            transaction_root=block.transactionsRoot,
                                            receipt_root=block.receiptsRoot,
                                            bloom=0,  # default value
                                            gas_used=0,  # set to zero
                                            extra_data=block.extraData,
                                            mix_hash=block.mixHash,
                                            nonce=block.nonce,
                                            base_fee_per_gas=block['baseFeePerGas'],
                                            )
    else:
        block_header = BlockHeader(difficulty=block.difficulty,
                                    block_number=block.number,
                                    gas_limit=block.gasLimit,
                                    timestamp=block.timestamp,
                                            coinbase=to_canonical_address(
                                                block.miner),  # default value
                                    parent_hash=block.parentHash,
                                    uncles_hash=block.uncles,
                                    state_root=block.stateRoot,
                                    transaction_root=block.transactionsRoot,
                                    receipt_root=block.receiptsRoot,
                                    bloom=0,  # default value
                                    gas_used=0,  # set to zero
                                    extra_data=block.extraData,
                                    mix_hash=block.mixHash,
                                    nonce=block.nonce,
                                )
    return block_header