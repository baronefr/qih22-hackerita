import numpy as np 
import matplotlib.pyplot as plt
import yaml

def QBER(list_A, list_B):
    return np.sum(list_A != list_B)/len(list_A)

def errorCorrectionEfficiency(QBER,table):
    if hasattr(QBER, "__len__"):
        error_correction_efficiency = np.zeros(len(QBER))
        for j in range(len(QBER)):
            error_correction_efficiency[j] = 0
            for i in range(len(table[0])):
                if QBER[j] < table[0][i] or i == 0:
                    error_correction_efficiency[j] = LDPC_ERROR_THRESHOLD_VS_EFFICIENCY_TABLE[1][i]
    else:
        error_correction_efficiency = 0
        for i in range(len(table[0])):
            if QBER < table[0][i] or i == 0:
                error_correction_efficiency = LDPC_ERROR_THRESHOLD_VS_EFFICIENCY_TABLE[1][i]
    return error_correction_efficiency

def binaryEntropy(p):
    if hasattr(p, "__len__"):
        p=np.array(p)
    h = -p*np.log2(p) - (1-p)*np.log2(1-p)
    if hasattr(h, "__len__"):
        h[p==0]=0
        h[p==1]=0
    else:
        if p == 0 or p== 1:
            h= 0
    return h

# from https://journals.aps.org/pra/pdf/10.1103/PhysRevA.104.022406
# sifted_key_rate = coincidence_rate * same_basis_prob
# QBER_key is the QBER in the key basis
# QBER_check is the QBER in the check basis
# error_correction_efficiency is the efficency of the error reconciliation protocol
def asymptoticSecretKeyRate(QBER_key,QBER_check,sifted_key_rate,error_correction_efficiency) :
    skr= sifted_key_rate*(1-binaryEntropy(QBER_key)/error_correction_efficiency-binaryEntropy(QBER_check))
    if hasattr(skr, "__len__"):
        return  skr*np.heaviside(skr,np.zeros(len(skr)))
    else:
        return max(skr,0)

#From https://arxiv.org/pdf/0901.2140.pdf :
LDPC_ERROR_THRESHOLD_VS_EFFICIENCY_TABLE = [[0.1071,0.0904,0.0766,0.0633,0.0504,0.0392,0.0298,0.0199,0.0109],[0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9]]

#qbers = np.arange(0,0.5,0.01)

#plt.figure()
#plt.plot(qbers,binaryEntropy(qbers))
#plt.show()

#plt.figure()
#plt.plot(qbers,errorCorrectionEfficiency(qbers,LDPC_ERROR_THRESHOLD_VS_EFFICIENCY_TABLE))
#plt.show()

#plt.figure()
#plt.plot(qbers,asymptoticSecretKeyRate(qbers,qbers,100,errorCorrectionEfficiency(qbers,LDPC_ERROR_THRESHOLD_VS_EFFICIENCY_TABLE)))
#plt.show()
with open("../raw_output/LAST/receiver_app_log.yaml", "r") as stream:
    try:
       receiver_log = yaml.safe_load(stream)
       receiver_outcomes = np.array(list(eval(receiver_log[0]['LOG'][12:])))
       receiver_basis = np.array(list(eval(receiver_log[1]['LOG'][15:])))
    except yaml.YAMLError as exc:
        print(exc)

with open("../raw_output/LAST/sender_app_log.yaml", "r") as stream:
    try:
       sender_log = yaml.safe_load(stream)
       sender_outcomes = np.array(list(eval(sender_log[0]['LOG'][14:])))
       sender_basis = np.array(list(eval(sender_log[1]['LOG'][18:])))
    except yaml.YAMLError as exc:
        print(exc)

print("raw key length: {}".format(len(sender_outcomes)))
sifted_indexes = receiver_basis == sender_basis
print("sifted key length: {}".format(np.sum(sifted_indexes)))
sender_list = sender_outcomes[sifted_indexes]
receiver_list = receiver_outcomes[sifted_indexes]
#print("equal elements: {}".format(np.sum(sender_list == receiver_list)))
#print("total elements: {}".format(len(sender_list)))
qber = QBER(sender_list,receiver_list)
print("QBER eve = {}".format(qber))
#print(sender_list==receiver_list)
skr = asymptoticSecretKeyRate(qber,qber,len(sender_list),errorCorrectionEfficiency(qber,LDPC_ERROR_THRESHOLD_VS_EFFICIENCY_TABLE))
print("secret key length = {}".format(skr))
 