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
                        c = 200, maxRunCount = 3, power = 2,
                        metric = "sqeuclidean", w = 0.5):
        #### parameters ###############################
        self.c = 2*(c//2) + 1 #  
        self.maxRunCount = maxRunCount
        self.metric = metric
        self.previous = None
        self.n_chroma = n_chroma
        self.power = power
        self.referenceChromas = referenceChromas
        self.recordedChromas = recordedChromas
        self.w = w
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
        self.extra = 0

    def align(self):

        while self.j < self.frameNumScore-1 and self.t < self.framenumaudio-1:
            # TODO j can get out of index towards the end of the audio.
            # TODO jj has to be limited to the length of the audio.x 
            # print(f"{self.t} / {self.framenumaudio}")
            newChroma = self.recordedChromas[self.t]
            self.U[:,:-1] = self.U[:,1:]
            self.U[:,-1] = newChroma # [:,0]
            
            

            

            aa = time.time()

             

            jj = np.max([self.startFrameJ, self.j - self.c//2 ])
            jjEnd = np.min([self.frameNumScore, self.j + self.c//2 + 1])

            # for k in range(jj, jjEnd):
            #     self.d[k, self.t] = np.linalg.norm(self.V[:,k] - self.U[:,-1])**2
            self.d[jj:jjEnd, self.t] = np.linalg.norm(self.V[:,jj:jjEnd] - self.U[:,-1:], axis = 0)**self.power

            # print(f"filled d from [{jj} to {jjEnd - 1}]")   

            
            # use extra to fill the remaining values on top
            startD = jj
            endD = np.min([self.j + self.c//2 - self.extra , self.frameNumScore - self.extra - 1])
            # if jump - 1 > 0:
            #     for k in range(np.min([self.j + self.c//2,self.frameNumScore]), np.min([self.j + self.c//2 + 1 + self.extra, self.frameNumScore])):
            #         self.d[k, self.t] = np.linalg.norm(self.V[:,k] - self.U[:,-1])**2
            #     endD = np.min([self.j + self.c//2 + self.extra + 1, self.frameNumScore])
            # elif jump - 1 < 0:
            #     for k in range(np.max([0,jj - self.extra]), jj):
            #         self.d[k, self.t] = np.linalg.norm(self.V[:,k] - self.U[:,-1])**2
            #     startD = np.max([0,jj - self.extra])
            # endD : endD + self.extra + 1
            if self.t>0:
                self.D[startD, self.t] = self.D[startD, self.t-1] + self.d[startD, self.t]

                # tmp1f = self.d[startD+1 : endD, self.t] + self.D[startD : endD-1, self.t]
                # tmp2f = self.w*self.d[startD+1 : endD, self.t] + self.D[startD : endD-1, self.t-1]
                # tmp3f = self.d[startD+1 : endD, self.t] + self.D[startD+1 : endD, self.t-1]

                # if not np.isfinite(tmp1f).all():
                #     logging.error(f'inf in tmp1')
                #     pdb.set_trace()
                #     raise
                # if not np.isfinite(tmp2f).all():
                #     logging.error(f'inf in tmp2')
                #     pdb.set_trace()
                #     raise
                # if not np.isfinite(tmp3f).all():
                #     logging.error(f'inf in tmp3')
                #     pdb.set_trace()
                #     raise

                for k in range(startD + 1, endD  ):
                # tmp1 = self.d[startD+1 : endD, self.t] + self.D[startD : endD-1, self.t]
                # tmp2 = self.w*self.d[startD+1 : endD, self.t] + self.D[startD : endD-1, self.t-1]
                # tmp3 = self.d[startD+1 : endD, self.t] + self.D[startD+1 : endD, self.t-1]
                # self.D[startD+1 : endD, self.t] = np.min([tmp1, tmp2, tmp3], axis = 0)
                    tmp1 = self.d[k, self.t] + self.D[k-1, self.t]
                    tmp2 = self.w*self.d[k, self.t] + self.D[k-1, self.t-1]
                    tmp3 = self.d[k, self.t] + self.D[k, self.t-1]
                    if tmp1 == np.inf:
                        logging.error(f"tmp1 is inf")
                        pdb.set_trace()
                    if tmp2 == np.inf:
                        logging.error(f"tmp2 is inf")
                        pdb.set_trace()
                    if tmp3 == np.inf:
                        logging.error(f"tmp3 is inf")
                        pdb.set_trace()
                    self.D[k, self.t] = np.min([tmp1, tmp2, tmp3])
                    if not np.isfinite(np.array([tmp1, tmp2, tmp3])).all():
                        logging.error(f'inf in J calc {np.array([tmp1, tmp2, tmp3])} {self.d[k, self.t]} {self.D[k, self.t-1]} {k} {self.t-1}')
                        pdb.set_trace()
                        raise
                
                

                for k in range(endD , endD + self.extra + 1):
                # self.D[endD : endD + self.extra + 1, self.t] = self.D[endD-1 : endD + self.extra , self.t] + self.d[endD : endD + self.extra + 1, self.t]
                    self.D[k, self.t] = self.D[k-1 , self.t] + self.d[k, self.t]
                    # print(f"calculated {k} {self.t}")
                    if self.D[k, self.t] == np.inf:
                        logging.error(f'inf in vertical calculation k = {k} t = {self.t}')
                        logging.error(f"tmp1 {self.d[k, self.t]} tmp2 {self.D[k-1, self.t]}")
                        raise
                if not np.isfinite(self.D[startD:endD+self.extra+1, self.t]).all():
                        logging.error(f'gamwww')
                        # logging.error(f"tmp1 {self.d[k, self.t]} tmp2 {self.D[k-1, self.t]} tmp3 {self.D[k-1, self.t-1]} tmp4 {self.D[k, self.t-1]}")
                        raise
            else:
                self.D[startD, self.t] = self.d[startD, self.t]
                for k in range(startD + 1, endD + 1 ):
                    self.D[k, self.t] = self.d[k, self.t] + self.D[k-1, self.t]
                self.D[endD + 1, self.t] = self.d[endD + 1, self.t] + self.D[endD , self.t]
                # pdb.set_trace()
                if not np.isfinite(self.D[startD:endD+1, self.t]).all():
                    logging.error(f'problem in start')
                    # logging.error(f"tmp1 {self.d[k, self.t]} tmp2 {self.D[k-1, self.t]} tmp3 {self.D[k-1, self.t-1]} tmp4 {self.D[k, self.t-1]}")
                    raise

            jump = self.getInc()

            self.extra = np.abs(jump - 1)

            print(f"J = {self.j} T = {self.t}, jump = {jump}")

            self.j = self.j + jump


            self.i += 1
            if self.i > len(self.pathOnline) - 1:
                print(f"Path Overflow")
                self.pathOverflow = True
                break
            # self.pathOnline[self.i,:] = [self.x, self.y]
            self.pathFront[self.i,:] = [self.t, self.j]

            self.t += 1
            
    def getInc(self):

        if self.t < 5:
            return 1
        tmp2 = self.D[:, self.t]
        jj = np.arange(len(tmp2))
        tmp2 = tmp2 / np.sqrt((jj+1)**2+(self.t)**2)
        self.new_j = np.argmin(tmp2)
        
        return np.min([np.max([self.new_j - self.j, 0]), 100])
        
        

#%%
if __name__ == "__main__" : 
    from utils_offline import resource_path, Params, getChromas
    from pathlib import Path
    from matplotlib import pyplot as plt
    # logging.getLogger().setLevel(logging.DEBUG)
    # Uncomment below for terminal log messages
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

    # logger = logging.getLogger('AlignerOffline')
    # logger.setLevel(logging.DEBUG)
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s - %(threadName)s - %(lineno)s: %(message)s', datefmt= '%H:%M:%S')

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
    # referenceAudioFile = Path("/home/xribene/Projects/ScoreFollower/resources/Pieces/Stravinsky/1_SoldiersMarch/Stravinsky_SoldiersMarch.wav")

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
    # referenceChromas2 = getChromas(referenceAudioFile, 
    #                             sr = 2*config.sr,
    #                             n_fft = 2*config.n_fft, 
    #                             hop_length = 2*config.hop_length,
    #                             window_length = 2*config.window_length,
    #                             chromaType = config.chromaType,
    #                             n_chroma = config.n_chroma,
    #                             norm = config.norm,
    #                             normAudio = True,
    #                             windowType = config.window_type,
    #                             chromafb = None,
    #                             magPower = config.magPower,
    #                             useZeroChromas = False
    #                             )

    repeats = np.ones((recordedChromas.shape[0]))
    repeats[600:900] = 2
    # repeats[800:900] = 2
    repeats[1500:2000] = 2
    recordedChromas = np.repeat(recordedChromas, list(repeats), axis=0)
    #%%
    aligner = AlignerOffline(referenceChromas, recordedChromas,
                                    n_chroma = config.n_chroma, 
                                    c = config.c, 
                                    maxRunCount = config.maxRunCount, 
                                    metric = config.metric,
                                    w = config.w_diag)

    #%%
    aligner.align()

    #%%

    print(f"durs J is {np.mean(aligner.dursJ)} durs T is {np.mean(aligner.dursT)}")
    print(f"distance is {aligner.D[aligner.j ,aligner.t-1]}")
    #%%
    plt.figure()
    plt.scatter(aligner.pathFront[:aligner.i,0], aligner.pathFront[:aligner.i,1], 0.1)

    plt.show()

    #%%
    from tslearn.metrics import dtw, dtw_path, dtw_path_from_metric
    from scipy.spatial.distance import cdist
    import scipy.io as sio
    # dtw_score = dtw(x, y)

    #%%
    x = recordedChromas
    y = referenceChromas
    # x = np.transpose(referenceChromas)
    # y = np.transpose(recordedChromas)
    # z = np.load("recordedChromas.npy")
    # dtw_path(ts1, ts2)[1] == np.sqrt(dtw_path_from_metric(ts1, ts2, metric="sqeuclidean")[1])

    path, dtw_score = dtw_path_from_metric(x,y, metric="sqeuclidean")
    # path, dtw_score = dtw_path(x,y)
    print(dtw_score)
    # plt.figure()
    pathArr = np.array(path)
    #%%
    plt.figure()
    plt.scatter(pathArr[:,0], pathArr[:,1], 0.1)
    plt.plot(pathArr[:,0], pathArr[:,1])
    plt.show()
    # %%
