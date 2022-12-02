# ========================================
#  QIH  >>  Hackathon
#  UniPD, AY 2022/23, Physics of Data
# ----------------------------------------
#   coder : Barone Francesco
#   dated : 01 December 2022
# ========================================
#  Code for entangled-based QKD
# ========================================


# %% ======================================================
#  setup
# =========================================================

import netsquid as ns
import pydynaa
import numpy as np

from netsquid.components import ClassicalChannel, QuantumChannel, FibreDelayModel, FixedDelayModel
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.components import QuantumMemory
from netsquid.components.component import Port
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks



ns.set_qstate_formalism(ns.QFormalism.DM)
ns.sim_reset()


# %% ======================================================
#  settings
# =========================================================

# define the measurement basis to use
MEAS_BASIS =  [
    {"name" : "01" , "op" : ns.Z },
    {"name" : "+-" , "op" : ns.X }
]

BATCH_CONCILIATION_SIZE = 5


# %% ======================================================
#  define entities
# =========================================================

def get_same_basis(mydata, mybasis, otherbasis) -> list:
    agree_bits = []
    for d, b, o in zip(mydata, mybasis, otherbasis):
        if( b == o ): agree_bits.append(d)
    return agree_bits


class Target(pydynaa.Entity):

    def __init__(self, name, channel_to_send, channel_to_recv):
        self.name = name

        # link RX & TX channel ports
        self.cch_sendp = channel_to_send.ports["send"]
        self.cch_recvp = channel_to_recv.ports["recv"]

        self.qmemory = QuantumMemory(name+"Memory", num_positions=1)
        self.qmemory.ports["qin0"].notify_all_input = True


        ## HANDLERS ----------------------------------
        # execute this function if receive qubit
        self._wait(pydynaa.EventHandler(self._handle_input_qubit),
                   entity=self.qmemory.ports["qin0"], event_type=Port.evtype_input)
        
        # execute this function if receive a string compare
        self.cch_recvp.bind_output_handler(self._handle_conciliation)


        ## BIT MEMORY ----------------------------------
        self.measure_results = []
        self.chosen_basis = []
        self.rcounter = 0
        self.last_conciliation = 0
        self.conciliated_bits = []


    def _handle_input_qubit(self, event):

        if self.rcounter - self.last_conciliation > BATCH_CONCILIATION_SIZE:
            self._init_conciliation()

        # make a random choice of measure basis
        #chosen_basis_idx = random.randint(0, len(MEAS_BASIS)-1) # if you use random
        chosen_basis_idx = np.random.randint(0, high=len(MEAS_BASIS)) # if use numpy
        measure_basis = MEAS_BASIS[chosen_basis_idx]

        mes, prb = self.qmemory.measure(positions=[0],
                                  observable=measure_basis['op'],
                                  discard=True)
        mesval = mes[0] # don't care about prb
        print("[{}] choose basis |{}>".format(self.name,measure_basis['name']),
              ' &  measures: {}'.format(mesval) )

        self.measure_results.append(mesval)
        self.chosen_basis.append(chosen_basis_idx)
        self.rcounter += 1
        return 0

    def _init_conciliation(self):
        print('[{}]'.format(self.name), 'send conciliation at qbit #{}'.format(self.rcounter) )
        self.cch_sendp.tx_input( [
                                    (self.last_conciliation, self.rcounter),
                                    self.chosen_basis[self.last_conciliation:self.rcounter]
                                 ]
                                )
        self.last_conciliation = self.rcounter

    def _handle_conciliation(self, message):
        range_idx, other_chosen_basis = message.items
        print('[{}]'.format(self.name), 'received conciliation in range', range_idx)
        self.conciliated_bits += get_same_basis(
                            self.measure_results[range_idx[0]:range_idx[1]], # measure results
                            self.chosen_basis[range_idx[0]:range_idx[1]], # mybasis 
                            other_chosen_basis # otherbasis
                          )
        # print comulative reconciliation
        #print('[{}]'.format(self.name), 'complete conciliation:', self.conciliated_bits)




# Bell 00 state generator
state_sampler = StateSampler([ks.b00], [1.0])


eve_source = QSource("Eve", state_sampler,      # generates Bell 00 state
                     frequency=100, num_ports=2,
                     timing_model=FixedDelayModel(delay=50),
                     status=SourceStatus.INTERNAL   # use internal sim clock
                    )



cchannelAB = ClassicalChannel("CChannelAB", length=4e-3,
                            models={"delay_model": FibreDelayModel()})

cchannelBA = ClassicalChannel("CChannelBA", length=4e-3,
                            models={"delay_model": FibreDelayModel()})



alice = Target("alyy", cchannelAB, cchannelBA)
bob = Target("boby", cchannelBA, cchannelAB)


def setup_network(alice, bob,
                  qsource, # the Eve's source
                  length=4e-3
                 ):

    qchannel_e2a = QuantumChannel("Eve->Alice", length=length/2,
                                  models={"delay_model": FibreDelayModel()})

    qchannel_e2b = QuantumChannel("Eve->Bob", length=length/2,
                                  models={"delay_model": FibreDelayModel()})

    qsource.ports['qout0'].connect(qchannel_e2a.ports['send'])
    qsource.ports['qout1'].connect(qchannel_e2b.ports['send'])

    alice.qmemory.ports['qin0'].connect(qchannel_e2a.ports['recv'])
    bob.qmemory.ports['qin0'].connect(qchannel_e2b.ports['recv'])

setup_network(alice, bob, eve_source)





# %% ======================================================
#  run simulation
# =========================================================

stats = ns.sim_run(end_time=1000)

# print conciliated bits
print('Alice:', alice.conciliated_bits)
print('Bob  :', bob.conciliated_bits)

print('conciled qbits:', len(alice.conciliated_bits) )
print('exchanged qbits:', alice.rcounter)



# %%
