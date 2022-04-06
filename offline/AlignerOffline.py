#%%
import logging
from syslog import LOG_WARNING
import numpy as np
import queue
from math import sqrt
import time
import pdb; 
from utils_offline import cosine_distance
from scipy.spatial.distance import cosine

#%%
class AlignerOffline():
    def __init__(self, referenceChromas, recordedChromas, n_chroma = 12, 
                        c = 200, maxRunCount = 3, 
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
        self.power = 1
        self.j_todo = 0
        self.j_todo_flag = False
        ##############################################
        # self.scoreChroma = score_chroma
        self.zeroChroma = np.ones((n_chroma,1)) / np.sqrt(12) # norm2

        self.pathOverflow = False

        self.frameNumScore = self.referenceChromas.shape[0]
        self.frameNum = self.referenceChromas.shape[0]

        self.framenumaudio = self.frameNumScore # * 2 # in matlab code they use self.c

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

        while self.j < self.frameNumScore-1:
                
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

            logging.debug(f"J = {self.j}, T = {self.t}")

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
                        
            # logging.debug(f"AFTER \n{self.D[:10,:10]}")
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
                logging.debug(f"Path Overflow")
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
# logging.getLogger().setLevel(logging.DEBUG)
# Uncomment below for terminal log messages
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

logger = logging.getLogger('AlignerOffline')
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

#%%
config = Params(Path(resource_path("configOffline.json")))

# pieceName = "Jetee"
pieceName = "Stravinsky"
# sectionName = "1_ThemeA"
sectionName = "1_SoldiersMarch"
sectionNameNoPrefix = sectionName.split("_")[1]
referenceChromas = np.load(Path(resource_path(f"../resources/Pieces/{pieceName}/{sectionName}/referenceAudioChromas_{pieceName}_{sectionNameNoPrefix}.npy")))
# audioFile = Path(resource_path(f"../resources/Pieces/{pieceName}/{sectionName}/testAudio/recodedJetee22050.wav"))
# audioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Jetee/1_ThemeA/testAudio/recordedJetee22050.wav")
audioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Stravinsky/1_SoldiersMarch/testAudio/SoldiersMarchSpeech22k.wav")
referenceAudioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Stravinsky/1_SoldiersMarch/Stravinsky_SoldiersMarch.wav")

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
                            useZeroChromas = False
                            )
referenceChromas2 = getChromas(referenceAudioFile, 
                            sr = 2*config.sr,
                            n_fft = 2*config.n_fft, 
                            hop_length = 2*config.hop_length,
                            window_length = 2*config.window_length,
                            chromaType = config.chromaType,
                            n_chroma = config.n_chroma,
                            norm = config.norm,
                            normAudio = True,
                            windowType = config.window_type,
                            chromafb = None,
                            magPower = config.magPower,
                            useZeroChromas = False
                            )
#%%
aligner = AlignerOffline(referenceChromas2, recordedChromas,
                                n_chroma = config.n_chroma, 
                                c = config.c, 
                                maxRunCount = config.maxRunCount, 
                                metric = config.metric,
                                w = config.w_diag)

#%%
aligner.align()

#%%

logging.debug(f"durs J is {np.mean(aligner.dursJ)} durs T is {np.mean(aligner.dursT)}")
logging.debug(f"distance is {aligner.D[aligner.j ,aligner.t]}")
#%%
plt.figure()
plt.scatter(aligner.pathFront[:aligner.i,0], aligner.pathFront[:aligner.i,1], 0.1)

plt.show()