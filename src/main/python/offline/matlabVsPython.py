#%%
from tslearn.metrics import dtw, dtw_path, dtw_path_from_metric
from scipy.spatial.distance import cdist
import scipy.io as sio
import numpy as np
import logging
import numpy as np
import queue
from utils_offline import getReferenceChromas
from pathlib import Path
from matplotlib import pyplot as plt
import time
import librosa.display
import librosa
from copy import copy, deepcopy
from pdb import set_trace as bp
from sklearn.metrics.pairwise import euclidean_distances
#%%
chromafbMat = sio.loadmat("C:\\Users\\xribene\\Projects\\code_matlab_2019\\F2CM.mat")['F2CM']#,mat_dtype =np.float32)
referenceChromasMat = sio.loadmat("C:\\Users\\xribene\\Projects\\code_matlab_2019\\referenceChromagram.mat")['referenceChromagram']#,mat_dtype =np.float32)
plt.imshow(referenceChromasMat[:,:100])

#%%
n_chroma = 12
norm =  2 # use 2 for matlab
windowType = 'hamming' # use hamming for matlab
n_fft = 2*4096 #
chromafb =  None#chromafbMat[:,:4097] #for matlab
magPower = 1
# wav = wav/np.sqrt(np.mean(wav**2))
referenceChromas = getReferenceChromas(Path("jeteeFF.wav"), 
                                                  sr = 44100,
                                                  n_fft = n_fft, 
                                                  hop_length = 1024,
                                                  window_length = 2048,
                                                  chromaType = "stft",
                                                  n_chroma = n_chroma,
                                                  norm = norm,
                                                  normAudio = True,
                                                  windowType = windowType,
                                                  chromafb = chromafb,
                                                  magPower = magPower
                                                )
recordedChromas = getReferenceChromas(Path("recordedJetee.wav"), 
                                                  sr = 44100,
                                                  n_fft = n_fft, 
                                                  hop_length = 1024,
                                                  window_length = 2048,
                                                  chromaType = "stft",
                                                  n_chroma = n_chroma,
                                                  norm = norm,
                                                  normAudio = False,
                                                  windowType = windowType,
                                                  chromafb = chromafb
                                                )
referenceChromasRepeat = np.repeat(referenceChromas, [15]*12, axis=1)
recordedChromasRepeat = np.repeat(recordedChromas, [15]*12, axis=1)
referenceChromasMatRepeat = np.repeat(referenceChromasMat, [15]*12, axis=0)
#%%
plt.imshow(np.transpose(referenceChromasRepeat[:1000,:])) # (1972, 180)
plt.figure()
plt.imshow(referenceChromasMatRepeat[:,:1000]) # (180,1972)
plt.figure()
plt.imshow(np.transpose(recordedChromasRepeat[:1000,:])) # (180,1972)

#%%
x = recordedChromas
y = referenceChromas

repeats = list(np.ones((y.shape[0])))
# for i in range(100,150):
#     repeats[i] += 1
for i in range(600,800):
    repeats[i] += 2
for i in range(1500,1700):
    repeats[i] += 1
# for i in range(800,1500):
#     repeats[i] += 1
y = np.repeat(y, repeats, axis=0)

# y = np.transpose(referenceChromasMat)
# z = np.load("recordedChromas.npy")
# dtw_path(ts1, ts2)[1] == np.sqrt(dtw_path_from_metric(ts1, ts2, metric="sqeuclidean")[1])

path, dtw_score = dtw_path_from_metric(x,y, metric="euclidean")
# path, dtw_score = dtw_path(x,y)
print(dtw_score)
# plt.figure()
pathArr = np.array(path)
plt.figure()
plt.scatter(pathArr[:,0], pathArr[:,1],1)
# plt.plot(pathArr[:,0], pathArr[:,1])
plt.show()
#%%
chromafbMat = sio.loadmat("C:\\Users\\xribene\\Projects\\code_matlab_2019\\F2CM.mat")['F2CM']#,mat_dtype =np.float32)

chromafb = librosa.filters.chroma(44100, n_fft, norm = 2,tuning=0, n_chroma=n_chroma)
#%%
plt.figure()
# for i in range(3):
plt.plot(chromafbMat[0])
plt.plot(chromafb[0])
plt.show()