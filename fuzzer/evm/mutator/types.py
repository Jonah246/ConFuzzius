from typing import TypedDict, List, Union

from eth_typing import ( 
    ChecksumAddress
    )

class AttackParams(TypedDict):
    address: ChecksumAddress
    mutateRate: float

class MutatorParams(TypedDict):
    attackRules: List[AttackParams]