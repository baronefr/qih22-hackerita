# ========================================
#  QIH  >>  Hackathon
#  UniPD, AY 2022/23, Physics of Data
# ----------------------------------------
#   coder : Barone Francesco
#   dated : 02 December 2022
# ========================================
#  Code for BBM92
# ========================================


# %% ======================================================
#  setup
# =========================================================


# %%
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

with_eve = True


# %% ======================================================
#  settings
# =========================================================

BATCH_CONCILIATION_SIZE = 5

# sifting rule
def get_same_basis(mydata, mybasis, otherbasis) -> list:
    agree_bits = []
    for d, b, o in zip(mydata, mybasis, otherbasis):
        if( b == o ): agree_bits.append(d)
    return agree_bits




# %% ======================================================
#  define entities
# =========================================================


class EntagledUser(pydynaa.Entity):

    def __init__(self, name, channel_to_send, channel_to_recv):
        self.name = name

        # link RX & TX channel ports
        self.cch_sendp = channel_to_send.ports["send"]
        self.cch_recvp = channel_to_recv.ports["recv"]

        self.qmemory = QuantumMemory(name+"Memory", num_positions=1)
        self.qmemory.ports["qin0"].notify_all_input = True


        ## HANDLERS ----------------------------------
        # execute this function if receive qubit
        self._wait(pydynaa.EventHandler(self._measure_qubit),
                   entity=self.qmemory.ports["qin0"], event_type=Port.evtype_input)
        
        # execute this function if receive a string compare
        self.cch_recvp.bind_output_handler(self._handle_conciliation)


        ## BIT MEMORY ----------------------------------
        self.measure_results = []
        self.chosen_basis = []
        self.rcounter = 0
        self.last_conciliation = 0
        self.conciliated_bits = []


    def _measure_qubit(self, event):

        if self.rcounter - self.last_conciliation > BATCH_CONCILIATION_SIZE:
            self._init_conciliation()
        
        # make a random choice of measure basis
        chosen_basis_idx = np.random.randint(0, high=2) # if use numpy

        if chosen_basis_idx:
            self.qmemory.operate(ns.H, positions=[0])
            measure_basis_name = 'x'
        else:
            measure_basis_name = '+'

        mes, prb = self.qmemory.measure(positions=[0],
                                  observable=ns.Z,
                                  discard=True)
        mesval = mes[0] # don't care about prb
        print("[{}] choose basis |{}>".format(self.name, measure_basis_name),
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




class EveUser(pydynaa.Entity):

    def __init__(self, name):
        self.name = name

        self.qmemory = QuantumMemory(name+"Memory", num_positions=1)
        self.qmemory.ports["qin0"].notify_all_input = True
        self.src = QSource("eve_source", status=SourceStatus.EXTERNAL)

        ## HANDLERS ----------------------------------
        # execute this function if receive qubit
        self._wait(pydynaa.EventHandler(self._hack_qubit),
                   entity=self.qmemory.ports["qin0"], event_type=Port.evtype_input)

        ## BIT MEMORY ----------------------------------
        self.measure_results = []
        self.chosen_basis = []
        self.rcounter = 0
        self.last_conciliation = 0
        self.conciliated_bits = []


    def _hack_qubit(self, event):

        # make a random choice of measure basis
        chosen_basis_idx = np.random.randint(0, high=2) # if use numpy

        if chosen_basis_idx:
            self.qmemory.operate(ns.H, positions=[0])
            measure_basis_name = 'x'
        else:
            measure_basis_name = '+'

        mes, prb = self.qmemory.measure(positions=[0],
                                  observable=ns.Z,
                                  discard=True)
        mesval = mes[0] # don't care about prb
        print("[{}] choose basis |{}>".format(self.name, measure_basis_name),
              ' &  measures: {}'.format(mesval) )
        
        self.measure_results.append(mesval)
        self.chosen_basis.append(chosen_basis_idx)
        self.rcounter += 1

        
        # set state to send
        if chosen_basis_idx: # measure in cross basis
            if mesval: state_eve = ns.qubits.ketstates.h1
            else:      state_eve = ns.qubits.ketstates.h0
        else:                # measure in plus basis
            if mesval: state_eve = ns.qubits.ketstates.s1
            else:      state_eve = ns.qubits.ketstates.s0

        self.src.state_sampler = StateSampler([state_eve], [1.0])
        self.src.trigger()

        print("[{}]".format(self.name),
              'sends', state_eve)

        return 0





# Bell 00 state generator
state_sampler = StateSampler([ks.b00], [1.0])


entangled_src = QSource("Gen", state_sampler,      # generates Bell 00 state
                     frequency=100, num_ports=2,
                     timing_model=FixedDelayModel(delay=50),
                     status=SourceStatus.INTERNAL   # use internal sim clock
                    )







# %% ======================================================
#  setup network
# =========================================================


cchannelAB = ClassicalChannel("CChannelAB", length=4e-3,
                            models={"delay_model": FibreDelayModel()})

cchannelBA = ClassicalChannel("CChannelBA", length=4e-3,
                            models={"delay_model": FibreDelayModel()})



alice = EntagledUser("alyy", cchannelAB, cchannelBA)
bob = EntagledUser("boby", cchannelBA, cchannelAB)
eve = EveUser("evy")

def setup_network(alice, bob,
                  qsource, # the entangled quantum source
                  length = 4e-3,
                  eve = None
                 ):

    qchannel_g2a = QuantumChannel("Gen->Alice", length=length/2,
                                  models={"delay_model": FibreDelayModel()})

    qchannel_g2b = QuantumChannel("Gen->Bob", length=length/2,
                                  models={"delay_model": FibreDelayModel()})

    
    qsource.ports['qout0'].connect(qchannel_g2a.ports['send'])
    qsource.ports['qout1'].connect(qchannel_g2b.ports['send'])

    # connect A
    alice.qmemory.ports['qin0'].connect(qchannel_g2a.ports['recv'])

    if eve is None:
        # connect B
        bob.qmemory.ports['qin0'].connect(qchannel_g2b.ports['recv'])
    else:
        qchannel_e2b = QuantumChannel("Eve->Bob", length=length/2,
                                  models={"delay_model": FibreDelayModel()})

        # connect E instead of B...
        eve.qmemory.ports['qin0'].connect(qchannel_g2b.ports['recv'])

        # ... and connect E to B
        eve.src.ports['qout0'].connect(qchannel_e2b.ports['send'])
        bob.qmemory.ports['qin0'].connect(qchannel_e2b.ports['recv'])

    
    
# setup the network layout
if with_eve:
    setup_network(alice, bob, entangled_src, eve=eve)
    basename = "with_eve_{}.npz"
else:
    setup_network(alice, bob, entangled_src)
    basename = "no_eve_{}.npz"





# %% ======================================================
#  run simulation
# =========================================================

stats = ns.sim_run(end_time=100000)

# print conciliated bits
print('Alice:', alice.conciliated_bits)
print('Bob  :', bob.conciliated_bits)

print('conciled qbits:', len(alice.conciliated_bits) )
print('exchanged qbits:', alice.rcounter)




# %% ======================================================
#  dump to file, for further analysis
# =========================================================

basename = "no_eve_{}.npz"

alice_basis = np.array(alice.chosen_basis, dtype=np.intc)
alice_meas = np.array(alice.measure_results, dtype=np.intc)
np.savez(basename.format("alice"), alice_basis, alice_meas)

bob_basis = np.array(bob.chosen_basis, dtype=np.intc)
bob_meas = np.array(bob.measure_results, dtype=np.intc)
np.savez(basename.format("bob"), bob_basis, bob_meas)

if with_eve:
    eve_basis = np.array(eve.chosen_basis, dtype=np.intc)
    eve_meas = np.array(eve.measure_results, dtype=np.intc)
    np.savez(basename.format("eve"), eve_basis, eve_meas)



# %% eof
print('end of program')
