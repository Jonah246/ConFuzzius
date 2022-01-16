#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from eth.abc import BlockHeaderAPI

from hexbytes import HexBytes
from typing import Optional, Set, cast
from copy import deepcopy

from eth import constants
from eth._utils.address import force_bytes_to_address
from eth.vm.computation import BaseComputation
from eth_hash.auto import keccak
from eth_typing import Address, Hash32
from eth_utils import to_bytes, to_normalized_address, to_hex, big_endian_to_int, int_to_big_endian

from eth.constants import BLANK_ROOT_HASH, EMPTY_SHA3
from eth.db.backends.base import BaseAtomicDB
from eth.db.account import AccountDB
from eth.typing import JournalDBCheckpoint
from eth.rlp.accounts import Account
from eth.tools._utils.normalization import to_int
from eth.validation import validate_uint256, validate_canonical_address, validate_is_bytes




from web3 import HTTPProvider
from web3 import Web3


from utils import settings


global BLOCK_ID
BLOCK_ID = "latest"

# STORAGE EMULATOR


class EmulatorAccountDB(AccountDB):
    def __init__(self, db: BaseAtomicDB, state_root: Hash32 = BLANK_ROOT_HASH) -> None:
        if settings.REMOTE_FUZZING and settings.RPC_HOST and settings.RPC_PORT:
            self._w3 = Web3(HTTPProvider('http://%s:%s' % (settings.RPC_HOST, settings.RPC_PORT)))
            self._remote = self._w3.eth
        else:
            self._remote = None
        self.state_root = BLANK_ROOT_HASH
        self._raw_store_db = db
        self.snapshot = None
        self._block_id = BLOCK_ID
        self._base_fee_per_gas = None

        self._dirty_accounts: Set[Address] = set()
        self._reset_access_counters()


    def set_snapshot(self, snapshot):
        self.snapshot = snapshot

    @property
    def state_root(self) -> Hash32:
        return self._state_root

    @state_root.setter
    def state_root(self, value: Hash32) -> None:
        self._state_root = value

    @property
    def _storage_emulator(self):
        return self._raw_store_db["storage"]

    @property
    def _account_emulator(self):
        return self._raw_store_db["account"]

    @property
    def _code_storage_emulator(self):
        return self._raw_store_db["code"]

    def set_block_header(self, header: BlockHeaderAPI):
        self._block = header

    def set_block_identifier(self, block_identifier: int, base_fee_per_gas: Optional[int] = None):
        self._block_id = block_identifier
        if base_fee_per_gas:
            self._base_fee_per_gas = base_fee_per_gas

    def get_storage(self, address: Address, slot: int, from_journal: bool = True) -> int:
        validate_canonical_address(address, title="Storage Address")
        validate_uint256(slot, title="Storage Slot")
        if address in self._storage_emulator and slot in self._storage_emulator[address] or not self._remote:
            try:
                return self._storage_emulator[address][slot]
            except KeyError:
                return 0
        else:
            result = self._remote.getStorageAt(address, slot, self._block_id)
            result = to_int(result.hex())
            self.set_storage(address, slot, result)
            if self.snapshot != None:
                if address not in self.snapshot["storage"]:
                    self.snapshot["storage"][address] = dict()
                self.snapshot["storage"][address][slot] = result
            return result

    def set_storage(self, address: Address, slot: int, value: int) -> None:
        validate_uint256(value, title="Storage Value")
        validate_uint256(slot, title="Storage Slot")
        validate_canonical_address(address, title="Storage Address")
        if address not in self._storage_emulator:
            self._storage_emulator[address] = dict()
        self._storage_emulator[address][slot] = value

        self._dirty_accounts.add(address)

    def delete_storage(self, address: Address) -> None:
        validate_canonical_address(address, title="Storage Address")
        if address in self._storage_emulator:
            del self._storage_emulator[address]

    def _get_account(self, address: Address) -> Account:
        if address in self._account_emulator:
            account = self._account_emulator[address]
        elif not self._remote:
            account = Account()
        else:
            code = self._remote.getCode(address, self._block_id)
            if code:
                code_hash = keccak(code)
                self._code_storage_emulator[code_hash] = code
                if self.snapshot != None:
                    self.snapshot["code"][code_hash] = code
            else:
                code_hash = EMPTY_SHA3
            account = Account(
                int(self._remote.getTransactionCount(address, self._block_id)),
                self._remote.getBalance(address, self._block_id),
                BLANK_ROOT_HASH,
                code_hash
            )
            if self.snapshot != None:
                self.snapshot["account"][address] = account
            self._set_account(address, account)
        return account


    def _has_account(self, address: Address) -> bool:
        return address in self._account_emulator

    def _set_account(self, address: Address, account: Account) -> None:
        self._account_emulator[address] = account

    def get_nonce(self, address: Address) -> int:
        validate_canonical_address(address, title="Storage Address")
        a = self._get_account(address)
        return a.nonce

    def set_nonce(self, address: Address, nonce: int) -> None:
        validate_canonical_address(address, title="Storage Address")
        validate_uint256(nonce, title="Nonce")
        account = self._get_account(address)
        self._set_account(address, account.copy(nonce=nonce))

    def increment_nonce(self, address: Address):
        current_nonce = self.get_nonce(address)
        self.set_nonce(address, current_nonce + 1)

    def get_balance(self, address: Address) -> int:
        validate_canonical_address(address, title="Storage Address")
        return self._get_account(address).balance

    def set_balance(self, address: Address, balance: int) -> None:
        validate_canonical_address(address, title="Storage Address")
        validate_uint256(balance, title="Account Balance")
        account = self._get_account(address)
        self._set_account(address, account.copy(balance=balance))

    def set_code(self, address: Address, code: bytes) -> None:
        validate_canonical_address(address, title="Storage Address")
        validate_is_bytes(code, title="Code")
        account = self._get_account(address)
        code_hash = keccak(code)
        self._code_storage_emulator[code_hash] = code
        self._set_account(address, account.copy(code_hash=code_hash))

    def get_code(self, address: Address) -> bytes:
        validate_canonical_address(address, title="Storage Address")
        code_hash = self.get_code_hash(address)
        if code_hash == EMPTY_SHA3:
            return b''
        elif code_hash in self._code_storage_emulator:
            return self._code_storage_emulator[code_hash]

    def get_code_hash(self, address: Address) -> Hash32:
        validate_canonical_address(address, title="Storage Address")
        account = self._get_account(address)
        return account.code_hash

    def delete_code(self, address: Address) -> None:
        validate_canonical_address(address, title="Storage Address")
        account = self._get_account(address)
        code_hash = account.code_hash
        self._set_account(address, account.copy(code_hash=EMPTY_SHA3))
        if code_hash in self._code_storage_emulator:
            del self._code_storage_emulator[code_hash]

    def account_is_empty(self, address: Address) -> bool:
        return not self.account_has_code_or_nonce(address) and self.get_balance(address) == 0

    def account_has_code_or_nonce(self, address):
        return self.get_nonce(address) != 0 or self.get_code_hash(address) != EMPTY_SHA3

    def account_exists(self, address: Address) -> bool:
        validate_canonical_address(address, title="Storage Address")
        return address in self._account_emulator

    def touch_account(self, address: Address) -> None:
        validate_canonical_address(address, title="Storage Address")
        account = self._get_account(address)
        self._set_account(address, account)

    def delete_account(self, address: Address) -> None:
        validate_canonical_address(address, title="Storage Address")
        self.delete_code(address)
        if address in self._storage_emulator:
            del self._storage_emulator[address]
        if address in self._account_emulator:
            del self._account_emulator[address]

    def record(self) -> BaseAtomicDB:
        import copy
        checkpoint = copy.deepcopy(self._raw_store_db)
        return checkpoint

    def discard(self, checkpoint: BaseAtomicDB) -> None:
        import copy
        self._raw_store_db = copy.deepcopy(checkpoint)

    def commit(self, checkpoint: JournalDBCheckpoint) -> None:
        pass

    def mark_storage_warm(self, address: Address, slot: int) -> None:
        return None


    def make_state_root(self) -> Hash32:
        return None

    def persist(self) -> None:
        # reset local storage trackers
        self._account_stores = {}
        self._dirty_accounts = set()
        self._accessed_accounts = set()
        self._accessed_bytecodes = set()


    def has_root(self, state_root: bytes) -> bool:
        return False

def get_block_hash_for_testing(self, block_number):
    if block_number >= self.block_number:
        return b''
    elif block_number < self.block_number - 256:
        return b''
    else:
        return keccak(to_bytes(text="{0}".format(block_number)))

    # else:
    #     raise Exception("mutator_params not found")



