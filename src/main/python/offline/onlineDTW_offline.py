#%%
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
import scipy.io as sio


#%%
def cosine_distance(a, b):
    if a.shape != b.shape:
        raise RuntimeError("array {} shape not match {}".format(a.shape, b.shape))
    if a.ndim==1:
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)
    elif a.ndim==2:
        a_norm = np.linalg.norm(a, axis=1, keepdims=True)
        b_norm = np.linalg.norm(b, axis=1, keepdims=True)
    else:
        raise RuntimeError("array dimensions {} not right".format(a.ndim))
    similiarity = np.dot(a, b.T)/(a_norm * b_norm) 
    dist = 1. - similiarity
    return dist

def _getInc(D, t, j, x, y, runCount, maxRunCount, previous):
    '''
    _getInc: takes input index, score index as arguments and returns a
    char where:
    B = both
    C = column
    R = row
    which indicates the direction of the next alignment point
    '''
    print(runCount)
    # if t < c:
    #     return "B", x, y
    # if runCount > maxRunCount:
    #     # print("akriiiiiiiiiiiiiiiii")
    #     if previous == "R":
    #         return "C", x, y
    #     else:
    #         return "R", x, y
    # ! matlab's code
    # tmp1 = D(J , 1:T);
    # tmp2 = D(1:J , T);
    # ! java's code
    # 		for(int i = 0; i < c; i ++){
    # 			tmp1[i] = D[J-i][T];//将其赋值给一个新的一维矩阵里，方便调用my math 算最小值，从而确定方向，谁小加谁
    # 		}
    # 		double colMin = MyMath.findMin(tmp1).value;		
    # 		// check row
    # 		for(int i = 0; i < c; i ++){
    # 			tmp2[i] = D[J][T-i];
    # 		}
    # 		double rowMin = MyMath.findMin(tmp2).value;
    # ! python code (matlab based)
    tmp1 = D[j, :t+1]
    # tmp1 = deepcopy(D[j, :t+1])
    tmp2 = D[:j+1, t]
    # tmp2 = deepcopy(D[:j+1, t])
    # for tt in range(len(tmp1)):
    #     tmp1[tt] = tmp1[tt] / np.sqrt(j**2+(tt+1)**2)

    tt = np.arange(len(tmp1))
    tmp1 = tmp1 / np.sqrt(j**2+(tt+1)**2)
    
    # for jj in range(len(tmp2)):
    #     tmp2[jj] = tmp2[jj] / np.sqrt((jj+1)**2+t**2)

    jj = np.arange(len(tmp2))
    tmp2 = tmp2 / np.sqrt((jj+1)**2+t**2)
    # ! python code (java based)
    # tmp1 = D[j, :t]
    # tmp2 = D[:j, t]

    # TODO in matlab's code there is a normalization step.
    m1 = np.min(tmp1)
    x = np.argmin(tmp1)
    m2 = np.min(tmp2)
    y = np.argmin(tmp2)

    if m1 < m2:
        y = j
    elif m1 > m2:
        x = t
    else:
        # if x!=y :
        #     print(f"{m1} {m2} {x} {y}")
        #     bp()
        x = t
        y = j

    # ! in dixon's paper the next 2 ifs are at the beggining of the 
    # ! function. In matlab's code they are at the end.
    # if t < c:
    #     return "B", x, y
    # if runCount > maxRunCount:
    #     print("akriiiiiiiiiiiiiiiii")
    #     if previous == "R":
    #         return "C", x, y
    #     else:
    #         return "R", x, y

    if t < c:
        return "B", x, y
    if runCount > maxRunCount:
        # print("akriiiiiiiiiiiiiiiii")
        if previous == "R":
            return "C", x, y
        else:
            return "R", x, y
    if x < t:
        return "R", x, y
    elif y < j:
        return "C", x, y
    else:
        return "B", x, y

#%%
# yy, _ = librosa.load("recordedJetee.wav", sr = 44100)
# D = librosa.stft(yy)  # STFT of y
# S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
# chroma = librosa.feature.chroma_cqt(y=yy, sr=44100)
# fig, ax = plt.subplots()
# img = librosa.display.specshow(chroma, y_axis='chroma', x_axis='time', ax=ax)
# ax.set(title='Chromagram demonstration')
# fig.colorbar(img, ax=ax)
#%%
n_chroma = 12
norm =  2 # use 2 for matlab
windowType = 'hamming' # use hamming for matlab
n_fft = 2*4096 #
chromafbMat = sio.loadmat("C:\\Users\\xribene\\Projects\\code_matlab_2019\\F2CM.mat")['F2CM']#,mat_dtype =np.float32)
chromafb = chromafbMat[:,:4097] #for matlab
magPower = 1
# wav = wav/np.sqrt(np.mean(wav**2))
# distance = np.linalg.norm
# distance = cosine_distance
# referenceChromas = getReferenceChromas(Path("/home/xribene/Projects/ScoreFollower/src/main/python/offline/jeteeFF.wav"), 
referenceChromas = getReferenceChromas(Path("jeteeFF.wav"), 
# referenceChromas = getReferenceChromas(Path("jetee4.mid"), 
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
# recordedChromas = getReferenceChromas(Path("jetee4.mid"), 
# recordedChromas = getReferenceChromas(Path("/home/xribene/Projects/ScoreFollower/src/main/python/offline/recordedJetee.wav"), 
# recordedChromas = getReferenceChromas(Path("jeteeFF.wav"), 
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
                                                  chromafb = chromafb,
                                                  magPower = magPower
                                                  )
# recordedChromas = referenceChromas
recordedChromas = np.load("recordedChromas.npy")
print(referenceChromas.shape)
print(recordedChromas.shape)
# import scipy.ndimage
# referenceChromas = scipy.ndimage.median_filter(referenceChromas, size = (3,1))
#%%
repeats = list(np.ones((referenceChromas.shape[0])))
# for i in range(100,150):
#     repeats[i] += 1
for i in range(600-1,800):
    repeats[i] += 2
for i in range(1500-1,1700):
    repeats[i] += 1
# for i in range(800,1500):
#     repeats[i] += 1
referenceChromas = np.repeat(referenceChromas, repeats, axis=0)
# recordedChromas = recordedChromas[100:]
#%%
# repeats = list(np.ones((987)))
# for i in range(100,150):
#     repeats[i] += 1
# for i in range(500,600):
#     repeats[i] += 1
# for i in range(800,950):
#     repeats[i] += 1
# referenceChromas = np.repeat(referenceChromas, repeats, axis=0)
#%%
c = 200 #  
maxRunCount = 20
previous =  None
V = np.transpose(referenceChromas)
j = 0

U = np.zeros((n_chroma, c)) # audio chromas
t = 0

x = 0
y = 0
w = 0.5
# chromaQueue = chromaBuffer
##############################################
# DscoreChroma = score_chroma

frameNumScore = referenceChromas.shape[0]
frameNum = referenceChromas.shape[0]

framenumaudio = frameNumScore # * 2 # in matlab code they use Dc

pathLenMax = frameNumScore + framenumaudio

# DchromaBuffer = np.zeros((12, Dc))
# DinputQueue = inputqueue
###############################################
#### distance matrices ########################
D = np.array(np.ones((pathLenMax, pathLenMax))* np.inf)
#this is a matrix of the cost of a path which terminates at point [x, y]
#print(DD)
d = np.array(np.ones((pathLenMax, pathLenMax))* np.inf)
# d[0,0] = 1
# D[0,0] = d[0,0]
#this is a matrix of the euclidean distance between frames of audio
###############################################
#### least cost path ##########################
pathOnlineIndex = 0
pathFront = np.zeros((pathLenMax, 2))
pathOnline = np.zeros((pathLenMax, 2))
pathNew = np.zeros((pathLenMax, 2))

#    .pathFront[0,:]= [1,1]
frameQueue = queue.Queue()

# .inputindex = 1
# .scoreindex = 1
# .fnum = 0
# .previous = None
needNewFrame = 1
runCount = 1
i = 0
bStart = 0
# cuelist = cuelist
# startTimer()

# @pyqtSlot()
cnt = 1
durs = []
debug=[]
try:
    while j < frameNumScore-1:
        aa = time.time()
        # logging.debug("J less than")
        #print(f'path online index is {pathOnlineIndex}')
        #print(f'score index (J) is {scoreindex}')

        if needNewFrame == 1: # and not inputQueue.empty():
            newChroma = recordedChromas[cnt]
            cnt += 1
            U[:,:-1] = U[:,1:]
            # print(f"{U[:,-1].shape} {newChroma.shape}")
            U[:,-1] = newChroma[:]
            # chromaBuffer(:,1:end-1) = chromaBuffer(:,2:end);
            # chromaBuffer(:,end) = chroma;
        
        if (t==0) and (j==0):
            d[0,0] = 0 #np.linalg.norm(V[:,0] - U[:,-1])
            # d[0,0] = cosine_distance(V[:,0], U[:,-1])

            D[0,0] = d[0,0]
        # ! do i need that ?
        # if t>c:
        needNewFrame = 0
        # prevD = deepcopy(D)
        direction, x, y = _getInc(D, t, j, x, y, runCount, maxRunCount, previous)
        # print(np.array_equal(prevD, D))
        # logging.debug(f"{direction}")
        # IF GetInc(t,j) != Row
        #     j := j + 1
        #     FOR k := t - c + 1 TO t
        #         IF k > 0
        #             EvaluatePathCost(k,j)
        
        if direction in ["C","B"]:
            t += 1
            needNewFrame = 1
            jj = np.max([0, j - c + 1])
            # ll == j+1-jj
            for k in range(jj, j+1): # range(jj, j+1):
                d[k, t] = np.linalg.norm(V[:,k] - U[:,-1])**2 # c-1
                # d[k, t] = np.sum((V[:,k] - U[:,-1])**2) # c-1
                # d[k, t] = cosine_distance(V[:,k], U[:,c-1])
            # if j > c-2:
            #     print(f"j={j} t={t} jj={jj} k={k} start={jj} end={j} length={len([i for i in range(jj,j+1)])}" )
            #     bp()
            D[jj, t] = D[jj, t-1] + d[jj, t]
            for k in range(jj+1, j+1):
                tmp1 = d[k, t] + D[k-1, t]
                tmp2 = w*d[k, t] + 1*D[k-1, t-1]
                tmp3 = d[k, t] + D[k, t-1]
                D[k, t] = np.min([tmp1, tmp2, tmp3])

        if direction in ["R","B"]:
            j += 1
            tt = np.max([0, t - c + 1])
            # ttt = np.max([1, t - c])
            # debug.append(tt)
            # ll = t+1-tt
            # logging.warning(f"{V.shape}")
            for k in range(tt, t+1): # range(tt, t+1):
                # print(f"j={j} t={t} tt={tt} k={k} start={tt-t+c-1} end={t-t+c-1} len={len([i for i in range(tt, t+1)])}" )
                # bp()
                # print(f"j={j} t={t} tt={tt} k={k} ind={k-t+c-1}" )
                if (k-t+c-1==-1):
                    # print("to be continued")
                    bp()
                    continue
                if (k-t+c-1==-1):
                    raise
                d[j, k] = np.linalg.norm(V[:,j] - U[:,k-t+c-1])**2 # k-t+c-1
                # d[j, k] = np.sum((V[:,j] - U[:,k-t+c-1])**2) # k-t+c-1

                # d[j, k] = cosine_distance(V[:,j], U[:,k-t+c-1])
            # if j > c-3:
            #     print(f"j={j} t={t} tt={tt} k={k} start={tt-t+c-1} end={t-t+c-1} len={len([i for i in range(tt, t+1)])}" )
                # bp()
            D[j, tt] = D[j-1, tt] + d[j, tt]
            for k in range(tt+1, t+1):
                tmp1 = d[j, k] + D[j, k-1]
                tmp2 = w*d[j, k] + 1*D[j-1, k-1]
                tmp3 = d[j, k] + D[j-1, k]
                D[j, k] = np.min([tmp1, tmp2, tmp3])

        # assert(runCount<11)
        # if direction in ["C","R"]:
        if direction == previous:
            runCount = runCount + 1
        else:
            runCount = 1
            # print("ZEROED")
        # TODO remove the next IF and add it here
        
        if direction != "B":
            previous = direction

        i += 1
        pathOnline[i,:] = [x, y]
        pathFront[i,:] = [t, j]
        pathNew[i,:] = [t, y]
        print(j)
        durs.append(time.time() - aa)
except Exception as e:
    print(e)
#%%
print(f"t is {t}")
print(np.mean(durs))
print(f"distance is {D[j,t]}")
# pathOnline.sort(axis = 0)

# plt.figure()
# plt.scatter(pathOnline[:i,0], pathOnline[:i,1])
# plt.plot(pathOnline[:i,0], pathOnline[:i,1])

plt.figure()
plt.scatter(pathFront[:i,0], pathFront[:i,1],0.1)
# plt.plot(pathFront[:i,0], pathFront[:i,1])

# plt.figure()
# plt.scatter(pathNew[:i,0], pathNew[:i,1])
# plt.plot(pathNew[:i,0], pathNew[:i,1])

plt.show()
#%%
from tslearn.metrics import dtw, dtw_path, dtw_path_from_metric
from scipy.spatial.distance import cdist
import scipy.io as sio
# dtw_score = dtw(x, y)
# matVariables = sio.loadmat("C:\\Users\\xribene\\Projects\\code_matlab_2019\\matlab.mat",mat_dtype =np.float32)
# recordedChromasMat = matVariables["recordedChromagram"]
# referenceChromasMat = matVariables["referenceChromagram"]
referenceChromasMat = sio.loadmat("C:\\Users\\xribene\\Projects\\code_matlab_2019\\referenceChromagram.mat")['referenceChromagram']#,mat_dtype =np.float32)

#%%
# x = recordedChromas
# y = referenceChromas
x = np.transpose(recordedChromasMat)
y = np.transpose(referenceChromasMat)
# z = np.load("recordedChromas.npy")
# dtw_path(ts1, ts2)[1] == np.sqrt(dtw_path_from_metric(ts1, ts2, metric="sqeuclidean")[1])

path, dtw_score = dtw_path_from_metric(x,y, metric="euclidean")
# path, dtw_score = dtw_path(x,y)
print(dtw_score)
# plt.figure()
pathArr = np.array(path)
plt.figure()
plt.scatter(pathArr[:,0], pathArr[:,1])
plt.plot(pathArr[:,0], pathArr[:,1])
plt.show()
# plt.scatter(pathNew[:i,0], pathNew[:i,1])
# plt.plot(pathNew[:i,0], pathNew[:i,1])


#%%
# plt.scatter(pathFront[:,0], pathFront[:,1])
print(debug)