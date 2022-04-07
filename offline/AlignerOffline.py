#%%
import logging
from syslog import LOG_WARNING
import numpy as np
import queue
# from math import sqrt
import time
import pdb; 
# from utils_offline import cosine_distance
# from scipy.spatial.distance import cosine

#%%
class AlignerOffline():
    def __init__(self, referenceChromas, recordedChromas, n_chroma = 12, 
                        c = 200, maxRunCount = 3, power = 2,
                        metric = "sqeuclidean", w = 0.5):
        #### parameters ###############################
        self.c = c #  
        self.maxRunCount = maxRunCount
        self.metric = metric
        self.previous = None
        self.n_chroma = n_chroma
        self.referenceChromas = referenceChromas
        self.recordedChromas = recordedChromas
        self.w = w
        self.power = power
        self.j_todo = 0
        self.j_todo_flag = False
        ##############################################
        # self.scoreChroma = score_chroma
        self.zeroChroma = np.ones((n_chroma,1)) / np.sqrt(12) # norm2

        self.pathOverflow = False

        self.frameNumScore = self.referenceChromas.shape[0]
        self.frameNum = self.referenceChromas.shape[0]

        self.framenumaudio = self.recordedChromas.shape[0] # * 2 # in matlab code they use self.c

        self.pathLenMax = self.frameNumScore + self.framenumaudio
        self.V = np.transpose(self.referenceChromas)
        self.j = 0
        
        self.U = np.ones((self.n_chroma, self.c)) / np.sqrt(12) # audio chromas
        self.t = 0

        self.x = 0
        self.y = 0
        ###############################################
        #### distance matrices ########################
        self.D = np.array(np.ones((self.pathLenMax, self.pathLenMax)) * np.inf)
        #this is a matrix of the cost of a path which terminates at point [x, y]
        #print(self.D)
        self.d = np.array(np.ones((self.pathLenMax, self.pathLenMax)) * np.inf)
        self.d[0,0] = 0
        self.D[0,0] = self.d[0,0]
        self.dMask = np.array(np.zeros((self.pathLenMax, self.pathLenMax)) )
        self.DMask = np.array(np.zeros((self.pathLenMax, self.pathLenMax)) )
        #this is a matrix of the euclidean distance between frames of audio
        ###############################################
        #### least cost path ##########################
        self.pathOnlineIndex = 0
        self.pathFront = np.zeros((self.pathLenMax, 2))
        self.pathOnline = np.zeros((self.pathLenMax, 2))
    #    self.pathFront[0,:]= [1,1]
        self.frameQueue = queue.Queue()
        # self.inputindex = 1
        # self.scoreindex = 1
        # self.fnum = 0
        # self.previous = None
        self.startFrameJ = 0
        self.startFrameT = 0
        self.needNewFrame = 1
        self.runCount = 1
        self.i = 0
        self.bStart = 0
        self.dursJ = []
        self.dursT = []

    def align(self):

        while self.j < self.frameNumScore-1 and self.t < self.framenumaudio-1:
                
            if self.needNewFrame == 1: # and not self.inputQueue.empty():
                newChroma = self.recordedChromas[self.t]
                self.U[:,:-1] = self.U[:,1:]
                self.U[:,-1] = newChroma # [:,0]
            

            self.needNewFrame = 0

            direction = self.getInc()

            if self.j_todo_flag:
                self.j = self.j_todo
                self.j_todo_flag = False
                self.d[self.j,self.t] = 0
                self.D[self.j,self.t] = 0
                self.startFrameJ = self.j
                self.startFrameT = self.t
                direction = 'B'

            print(f"J = {self.j}, T = {self.t}")

            aa = time.time()
            if direction in ["C","B"]:
                self.t += 1
                self.needNewFrame = 1
                jj = np.max([self.startFrameJ, self.j - self.c+1])
                # for k in range(jj, self.j+1):
                #     self.d[k, self.t] = np.linalg.norm(self.V[:,k] - self.U[:,-1])**2
                #     # self.d[k, self.t] = cosine(self.V[:,k], self.U[:,-1])**2

                self.d[jj:(self.j+1), self.t] = np.linalg.norm(self.V[:,jj:(self.j+1)] - self.U[:,-1:], axis = 0)**self.power
                
                # if np.allclose(self.dTest[jj:(self.j+1), self.t], self.d[jj:(self.j+1), self.t] ) is False:
                #     pdb.set_trace()

                self.D[jj, self.t] = self.D[jj, self.t-1] + self.d[jj, self.t]
                
                tmp1 = self.d[jj+1: self.j+1, self.t] + self.D[jj: self.j, self.t]
                tmp2 = self.w*self.d[jj+1: self.j+1, self.t] + self.D[jj: self.j, self.t-1]
                tmp3 = self.d[jj+1: self.j+1, self.t] + self.D[jj+1: self.j+1, self.t-1]
                self.D[jj+1: self.j+1, self.t] = np.min([tmp1, tmp2, tmp3], axis = 0)

                # for k in range(jj+1, self.j+1):
                #     tmp1 = self.d[k, self.t] + self.D[k-1, self.t]
                #     tmp2 = self.w*self.d[k, self.t] + self.D[k-1, self.t-1]
                #     tmp3 = self.d[k, self.t] + self.D[k, self.t-1]
                #     self.D[k, self.t] = np.min([tmp1, tmp2, tmp3])
                #     if not np.isfinite(np.min([tmp1, tmp2, tmp3])).all():
                #         logging.error(f'inf in T calc')
                #         raise

            if direction in ["R","B"]:
                self.j += 1
                tt = np.max([self.startFrameT, self.t - self.c + 1])

                # for k in range(tt, self.t+1):
                #     self.d[self.j, k] = np.linalg.norm(self.V[:,self.j] - self.U[:,k-self.t+self.c-1])**2
                #     # print(f"V is {self.V[:,self.j]} \n U is {self.U[:,k-self.t+self.c-1]} \n dist is {cosine_distance(self.V[:,self.j], self.U[:,k-self.t+self.c-1])}")
                #     # self.d[self.j, k] = cosine(self.V[:,self.j], self.U[:,k-self.t+self.c-1])**2
                
                self.d[self.j, tt:(self.t+1)] = np.linalg.norm(np.expand_dims(self.V[:,self.j],axis=1) - self.U[:,(tt-self.t+self.c-1):(self.t+1-self.t+self.c-1)], axis = 0)**self.power
                
                # if self.j > 10 and self.t > 10 and np.allclose(self.dTest[self.j, tt:(self.t+1)], self.d[self.j, tt:(self.t+1)] ) is False:
                #     pdb.set_trace()
                self.D[self.j, tt] = self.D[self.j-1, tt] + self.d[self.j, tt]
                
                tmp1 = self.d[self.j, tt+1: self.t+1] + self.D[self.j, tt: self.t]
                tmp2 = self.w*self.d[self.j, tt+1: self.t+1] + self.D[self.j-1, tt: self.t]
                tmp3 = self.d[self.j, tt+1: self.t+1] + self.D[self.j-1, tt+1: self.t+1]
                self.D[self.j, tt+1: self.t+1] = np.min([tmp1, tmp2, tmp3], axis = 0)

                # for k in range(tt+1, self.t+1):
                #     tmp1 = self.d[self.j, k] + self.D[self.j, k-1]
                #     tmp2 = self.w*self.d[self.j, k] + self.D[self.j-1, k-1]
                #     tmp3 = self.d[self.j, k] + self.D[self.j-1, k]
                #     self.D[self.j, k] = np.min([tmp1, tmp2, tmp3])
                #     if not np.isfinite(np.min([tmp1, tmp2, tmp3])).all():
                #         logging.error(f'inf in J calc')
                #         raise
                        
            # print(f"AFTER \n{self.D[:10,:10]}")
            # pdb.set_trace()

            if direction == 'B':
                self.runCount = 1
            else:
                if direction == self.previous:
                    self.runCount += 1
                else:
                    self.runCount = 1
            self.previous = direction

            # if direction == self.previous:
            #     self.runCount = self.runCount + 1
            # else:
            #     self.runCount = 1
            
            # if direction != "B":
            #     self.previous = direction

            self.i += 1
            if self.i > len(self.pathOnline) - 1:
                print(f"Path Overflow")
                self.pathOverflow = True
                break
            self.pathOnline[self.i,:] = [self.x, self.y]
            self.pathFront[self.i,:] = [self.t, self.j]

            if direction == "R":
                self.dursJ.append(time.time() - aa)
            elif direction == 'C':
                self.dursT.append(time.time() - aa)
            
            
    def getInc(self):

        # TODO tmp1 and tmp2 include infs when t/j > self.c
        # TODO it's ok because we use np.min. But maybe we should contrain this.
        tmp1 = self.D[self.j, :self.t+1]
        tmp2 = self.D[0:self.j+1, self.t]
        try:
            if np.isinf(tmp1).all():
                logging.error(f'all are INF in tmp1')
                raise
            if np.isinf(tmp2).all():
                logging.error(f'all areINF in tmp2 j= 0:{self.j+1}, t={self.t}')
                print(self.D[:10,:10])
                print(tmp2)
                raise
        except:
            pdb.set_trace()
            raise

        tt = np.arange(len(tmp1))
        tmp1 = tmp1 / np.sqrt(self.j**2+(tt+1)**2)
        jj = np.arange(len(tmp2))
        tmp2 = tmp2 / np.sqrt((jj+1)**2+self.t**2)

        m1 = np.min(tmp1)
        self.x = np.argmin(tmp1)
        m2 = np.min(tmp2)
        self.y = np.argmin(tmp2)

        if m1 < m2:
            self.y = self.j
        elif m1 > m2:
            self.x = self.t
        else:
            self.x = self.t
            self.y = self.j
        
        if self.t < 5:
            return "B"
        if self.runCount > self.maxRunCount:
            if self.previous == "R":
                return "C"
            # else: # TODO how about elif self.previous == 'C'
            elif self.previous == "C":
                return "R"

        if self.x < self.t:
            return "R"
        elif self.y < self.j:
            return "C"
        else:
            return "B"

#%%
# if __name__ == "__main__" : 
from utils_offline import resource_path, Params, getChromas
from pathlib import Path
from matplotlib import pyplot as plt
from AlignerNewOffline import AlignerOffline as AlignerNewOffline
#%%
config = Params(Path(resource_path("configOffline.json")))

# pieceName = "Jetee"
pieceName = "Stravinsky"
# sectionName = "1_ThemeA"
sectionName = "1_SoldiersMarch"
sectionNameNoPrefix = sectionName.split("_")[1]
# referenceChromas = np.load(Path(resource_path(f"../resources/Pieces/{pieceName}/{sectionName}/referenceAudioChromas_{pieceName}_{sectionNameNoPrefix}.npy")))
# audioFile = Path(resource_path(f"../resources/Pieces/{pieceName}/{sectionName}/testAudio/recodedJetee22050.wav"))
# audioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Jetee/1_ThemeA/testAudio/recordedJetee22050.wav")
# audioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Stravinsky/1_SoldiersMarch/testAudio/SoldiersMarchSpeech22k.wav")
audioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Stravinsky/1_SoldiersMarch/testAudio/MultiSpeedRecordingSpeech22k.wav")
referenceAudioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Stravinsky/1_SoldiersMarch/Stravinsky_SoldiersMarch.wav")
# audioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Stravinsky/1_SoldiersMarch/testAudio/Stravinsky_SoldiersMarch22k.wav")
referenceMidiFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Stravinsky/1_SoldiersMarch/Stravinsky_SoldiersMarch.mid")
fmin = 60
recordedChromas = getChromas(audioFile, 
                            sr = config.sr,
                            n_fft = config.n_fft, 
                            hop_length = config.hop_length,
                            window_length = config.window_length,
                            chromaType = config.chromaType,
                            n_chroma = config.n_chroma,
                            norm = config.norm,
                            normAudio = True,
                            windowType = config.window_type,
                            chromafb = None,
                            magPower = config.magPower,
                            useZeroChromas = False,
                            fmin = fmin
                            )
recordedChromasCqt = getChromas(audioFile, 
                            sr = config.sr,
                            n_fft = config.n_fft, 
                            hop_length = config.hop_length,
                            window_length = config.window_length,
                            chromaType = "cqt",
                            n_chroma = config.n_chroma,
                            norm = config.norm,
                            normAudio = True,
                            windowType = config.window_type,
                            chromafb = None,
                            magPower = config.magPower,
                            useZeroChromas = False,
                            fmin = fmin
                            )

referenceChromas = getChromas(referenceAudioFile, 
                            sr = 2*config.sr,
                            n_fft = 2*config.n_fft, 
                            hop_length = 2*config.hop_length,
                            window_length = 2*config.window_length,
                            chromaType = "stft",
                            n_chroma = config.n_chroma,
                            norm = config.norm,
                            normAudio = True,
                            windowType = config.window_type,
                            chromafb = None,
                            magPower = config.magPower,
                            useZeroChromas = False,
                            fmin = fmin
                            )
referenceChromasMidi = getChromas(referenceMidiFile, 
                            sr = 2*config.sr,
                            n_fft = 2*config.n_fft, 
                            hop_length = 2*config.hop_length,
                            window_length = 2*config.window_length,
                            chromaType = "stft",
                            n_chroma = config.n_chroma,
                            norm = config.norm,
                            normAudio = True,
                            windowType = config.window_type,
                            chromafb = None,
                            magPower = config.magPower,
                            useZeroChromas = False,
                            fmin = fmin
                            )
referenceChromasCqt = getChromas(referenceAudioFile, 
                            sr = 2*config.sr,
                            n_fft = 2*config.n_fft, 
                            hop_length = 2*config.hop_length,
                            window_length = 2*config.window_length,
                            chromaType = "cqt",
                            n_chroma = config.n_chroma,
                            norm = config.norm,
                            normAudio = True,
                            windowType = config.window_type,
                            chromafb = None,
                            magPower = config.magPower,
                            useZeroChromas = False,
                            fmin = fmin
                            )
referenceChromasCqt = np.transpose(referenceChromasCqt)
recordedChromasCqt = np.transpose(recordedChromasCqt)
referenceChromasMidi = np.transpose(referenceChromasMidi)

repeats = np.ones((referenceChromas.shape[0]))
repeats[600:900] = 2
repeats[3000:3500] = 2
referenceChromas = np.repeat(referenceChromas, list(repeats), axis=0)

repeats = np.ones((referenceChromasCqt.shape[0]))
a1 = 600
a2 = 900
b1 = 3000
b2 = 3500
repeats[a1:a2] = 2
repeats[b1:b2] = 2
verts = [a1,a2+(a2-a1),b1+a2-a1, b2 + a2-a1 + b2 - b1]
referenceChromasCqt = np.repeat(referenceChromasCqt, list(repeats), axis=0)

repeats = np.ones((referenceChromasMidi.shape[0]))
repeats[a1:a2] = 2
repeats[b1:b2] = 2
referenceChromasMidi = np.repeat(referenceChromasMidi, list(repeats), axis=0)

#%%
aligner = AlignerOffline(referenceChromasMidi, recordedChromas + 0.0*np.random.randn(*recordedChromas.shape),
                                n_chroma = config.n_chroma, 
                                c = config.c, 
                                maxRunCount = config.maxRunCount, 
                                metric = config.metric,
                                power = 2,
                                w = 0.3)
#%%
alignerNew = AlignerNewOffline(referenceChromas, recordedChromas ,
                                n_chroma = config.n_chroma, 
                                c = config.c, 
                                maxRunCount = config.maxRunCount, 
                                metric = config.metric,
                                power = 2,
                                w = 0.5)

#%%
aligner.align()
#%%
alignerNew.align()

#%%

print(f"durs J is {np.mean(aligner.dursJ)} durs T is {np.mean(aligner.dursT)}")
print(f"distance is {aligner.D[aligner.j ,aligner.t]}")
#%%
print(f"durs J is {np.mean(alignerNew.dursJ)} durs T is {np.mean(alignerNew.dursT)}")
print(f"distanceNew is {alignerNew.D[alignerNew.j ,alignerNew.t-1]}")
    
#%%
from tslearn.metrics import dtw, dtw_path, dtw_path_from_metric
from scipy.spatial.distance import cdist
import scipy.io as sio
# dtw_score = dtw(x, y)

#%%
x = recordedChromas
xCqt = recordedChromasCqt
yCqt = referenceChromasCqt
y = referenceChromas
yMidi = referenceChromasMidi
# x = np.transpose(referenceChromas)
# y = np.transpose(recordedChromas)
# z = np.load("recordedChromas.npy")
# dtw_path(ts1, ts2)[1] == np.sqrt(dtw_path_from_metric(ts1, ts2, metric="sqeuclidean")[1])

path, dtw_score = dtw_path_from_metric(x,y, metric="euclidean")
pathCqt, dtw_scoreCqt = dtw_path_from_metric(x,yCqt, metric="euclidean")
pathCqt2, dtw_scoreCqt2 = dtw_path_from_metric(xCqt,yCqt, metric="euclidean")
pathMidi, dtw_scoreMidi = dtw_path_from_metric(x,yMidi, metric="sqeuclidean")

# 'l2', 'l1', 'manhattan', 'cityblock', 'braycurtis', 'canberra', 'chebyshev', 
# 'correlation', 'cosine', 'dice', 'hamming', 'jaccard', 'kulsinski',
#  'mahalanobis', 'matching', 'minkowski', 'rogerstanimoto', 'russellrao',
#   'seuclidean', 'sokalmichener', 'sokalsneath', 'sqeuclidean', 'yule', 
#   'wminkowski', 'nan_euclidean', 'haversine'
# path, dtw_score = dtw_path(x,y)
print(dtw_score)
print(dtw_scoreCqt)
print(dtw_scoreCqt2)
print(dtw_scoreMidi)

# plt.figure()
pathArr = np.array(path)
pathArrCqt = np.array(pathCqt)
pathArrCqt2 = np.array(pathCqt2)
pathArrMidi = np.array(pathMidi)

#%%
plt.figure()
line1 = plt.scatter(pathArr[:,0], pathArr[:,1], 0.1,  linewidth=1)
line1Cqt = plt.scatter(pathArrCqt[:,0], pathArrCqt[:,1], 0.1,  linewidth=1)
line1Cqt2 = plt.scatter(pathArrCqt2[:,0], pathArrCqt2[:,1], 0.1,  linewidth=1)
line2 = plt.scatter(aligner.pathFront[:aligner.i,0], aligner.pathFront[:aligner.i,1], 0.1, linewidth=2)
# line3 = plt.scatter(alignerNew.pathFront[:alignerNew.i,0], alignerNew.pathFront[:alignerNew.i,1], 0.1, linewidth=2)

for vert in verts:
    plt.axhline(y=vert)
plt.legend((line1, line1Cqt, line2, line3), ('offline', 'offlineCqt', 'offlineCqt2','online'), loc='lower right', shadow=True)

# plt.plot(pathArr[:,0], pathArr[:,1])
# plt.show()

# plt.figure()
# line2 = plt.scatter(aligner.pathFront[:aligner.i,0], aligner.pathFront[:aligner.i,1], 0.1, linewidth=2)
# line3 = plt.scatter(alignerNew.pathFront[:alignerNew.i,0], alignerNew.pathFront[:alignerNew.i,1], 0.1, linewidth=2)

# plt.legend((line1, line2, line3), ('offline', 'online','onlineNew'), loc='lower right', shadow=True)


plt.show()
# %%
