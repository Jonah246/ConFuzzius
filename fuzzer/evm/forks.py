from eth.chains.mainnet import MainnetHomesteadVM
from eth.vm.forks import FrontierVM, TangerineWhistleVM, SpuriousDragonVM, ByzantiumVM, PetersburgVM, LondonVM, ArrowGlacierVM
from eth.vm.forks.arrow_glacier import ArrowGlacierState
from eth.vm.forks.arrow_glacier.computation import ArrowGlacierComputation
from eth.vm.forks.london import LondonState
from eth.vm.forks.london.computation import LondonComputation
from eth.vm.forks.byzantium import ByzantiumState
from eth.vm.forks.byzantium.computation import ByzantiumComputation
from eth.vm.forks.frontier import FrontierState
from eth.vm.forks.frontier.computation import FrontierComputation
from eth.vm.forks.homestead import HomesteadState
from eth.vm.forks.homestead.computation import HomesteadComputation
from eth.vm.forks.petersburg import PetersburgState
from eth.vm.forks.petersburg.computation import PetersburgComputation
from eth.vm.forks.spurious_dragon import SpuriousDragonState
from eth.vm.forks.spurious_dragon.computation import SpuriousDragonComputation
from eth.vm.forks.tangerine_whistle import TangerineWhistleState
from eth.vm.forks.tangerine_whistle.computation import TangerineWhistleComputation

from .computation import fuzz_apply_computation
from .storage_emulation import get_block_hash_for_testing, EmulatorAccountDB

# FRONTIER
FrontierComputationForFuzzTesting = FrontierComputation.configure(
    __name__='FrontierComputationForFuzzTesting',
    apply_computation=fuzz_apply_computation,
)
FrontierStateForFuzzTesting = FrontierState.configure(
    __name__='FrontierStateForFuzzTesting',
    get_ancestor_hash=get_block_hash_for_testing,
    computation_class=FrontierComputationForFuzzTesting,
    account_db_class=EmulatorAccountDB,
)
FrontierVMForFuzzTesting = FrontierVM.configure(
    __name__='FrontierVMForFuzzTesting',
    _state_class=FrontierStateForFuzzTesting,
)

# HOMESTEAD
HomesteadComputationForFuzzTesting = HomesteadComputation.configure(
    __name__='HomesteadComputationForFuzzTesting',
    apply_computation=fuzz_apply_computation,
)
HomesteadStateForFuzzTesting = HomesteadState.configure(
    __name__='HomesteadStateForFuzzTesting',
    get_ancestor_hash=get_block_hash_for_testing,
    computation_class=HomesteadComputationForFuzzTesting,
    account_db_class=EmulatorAccountDB,
)
HomesteadVMForFuzzTesting = MainnetHomesteadVM.configure(
    __name__='HomesteadVMForFuzzTesting',
    _state_class=HomesteadStateForFuzzTesting,
)

# TANGERINE WHISTLE
TangerineWhistleComputationForFuzzTesting = TangerineWhistleComputation.configure(
    __name__='TangerineWhistleComputationForFuzzTesting',
    apply_computation=fuzz_apply_computation,
)
TangerineWhistleStateForFuzzTesting = TangerineWhistleState.configure(
    __name__='TangerineWhistleStateForFuzzTesting',
    get_ancestor_hash=get_block_hash_for_testing,
    computation_class=TangerineWhistleComputationForFuzzTesting,
    account_db_class=EmulatorAccountDB,
)
TangerineWhistleVMForFuzzTesting = TangerineWhistleVM.configure(
    __name__='TangerineWhistleVMForFuzzTesting',
    _state_class=TangerineWhistleStateForFuzzTesting,
)

# SPURIOUS DRAGON
SpuriousDragonComputationForFuzzTesting = SpuriousDragonComputation.configure(
    __name__='SpuriousDragonComputationForFuzzTesting',
    apply_computation=fuzz_apply_computation,
)
SpuriousDragonStateForFuzzTesting = SpuriousDragonState.configure(
    __name__='SpuriousDragonStateForFuzzTesting',
    get_ancestor_hash=get_block_hash_for_testing,
    computation_class=SpuriousDragonComputationForFuzzTesting,
    account_db_class=EmulatorAccountDB,
)
SpuriousDragonVMForFuzzTesting = SpuriousDragonVM.configure(
    __name__='SpuriousDragonVMForFuzzTesting',
    _state_class=SpuriousDragonStateForFuzzTesting,
)

# BYZANTIUM
ByzantiumComputationForFuzzTesting = ByzantiumComputation.configure(
    __name__='ByzantiumComputationForFuzzTesting',
    apply_computation=fuzz_apply_computation,
)
ByzantiumStateForFuzzTesting = ByzantiumState.configure(
    __name__='ByzantiumStateForFuzzTesting',
    get_ancestor_hash=get_block_hash_for_testing,
    computation_class=ByzantiumComputationForFuzzTesting,
    account_db_class=EmulatorAccountDB,
)
ByzantiumVMForFuzzTesting = ByzantiumVM.configure(
    __name__='ByzantiumVMForFuzzTesting',
    _state_class=ByzantiumStateForFuzzTesting,
)

# PETERSBURG
PetersburgComputationForFuzzTesting = PetersburgComputation.configure(
    __name__='PetersburgComputationForFuzzTesting',
    apply_computation=fuzz_apply_computation,
)
PetersburgStateForFuzzTesting = PetersburgState.configure(
    __name__='PetersburgStateForFuzzTesting',
    get_ancestor_hash=get_block_hash_for_testing,
    computation_class=PetersburgComputationForFuzzTesting,
    account_db_class=EmulatorAccountDB,
)
PetersburgVMForFuzzTesting = PetersburgVM.configure(
    __name__='PetersburgVMForFuzzTesting',
    _state_class=PetersburgStateForFuzzTesting,
)


# LONDON
LondonComputationForFuzzTesting = LondonComputation.configure(
    __name__='LondonComputationForFuzzTesting',
    apply_computation=fuzz_apply_computation,
)
LondonStateForFuzzTesting = LondonState.configure(
    __name__='LondonStateForFuzzTesting',
    get_ancestor_hash=get_block_hash_for_testing,
    computation_class=LondonComputationForFuzzTesting,
    account_db_class=EmulatorAccountDB,
)
LondonVMForFuzzTesting = LondonVM.configure(
    __name__='LondonVMForFuzzTesting',
    _state_class=LondonStateForFuzzTesting,
)


# ArrowGlacier
ArrowGlacierComputationForFuzzTesting = ArrowGlacierComputation.configure(
    __name__='LondonComputationForFuzzTesting',
    apply_computation=fuzz_apply_computation,
)
ArrowGlacierStateForFuzzTesting = ArrowGlacierState.configure(
    __name__='ArrowGlacierStateForFuzzTesting',
    get_ancestor_hash=get_block_hash_for_testing,
    computation_class=ArrowGlacierComputationForFuzzTesting,
    account_db_class=EmulatorAccountDB,
)
ArrowGlacierVMForFuzzTesting = ArrowGlacierVM.configure(
    __name__='ArrowGlacierVMForFuzzTesting',
    _state_class=ArrowGlacierStateForFuzzTesting,
)
