import logging
from PyQt5.QtCore import (QObject, pyqtSignal, QTimer, pyqtSlot, QTimer
                           )
import numpy as np
import queue
from math import sqrt
import time

class Aligner(QObject):
    signalToGUIThread = pyqtSignal(object)
    signalToOSCclient = pyqtSignal(int)
    signalEnd = pyqtSignal()
    def __init__(self, referenceChromas, chromaBuffer):
        QObject.__init__(self)
        #### parameters ###############################
        self.c = 200 #  
        self.maxRunCount = 3
        self.previous = None
        self.V = np.transpose(referenceChromas)
        self.j = 0
        
        self.U = np.zeros((12, self.c)) # audio chromas
        self.t = 0

        self.x = 0
        self.y = 0
        self.chromaQueue = chromaBuffer
        ##############################################
        # self.scoreChroma = score_chroma

        self.frameNumScore = referenceChromas.shape[0]
        self.frameNum = referenceChromas.shape[0]

        self.framenumaudio = self.frameNumScore # * 2 # in matlab code they use self.c

        self.pathLenMax = self.frameNumScore + self.framenumaudio

        # self.chromaBuffer = np.zeros((12, self.c))
        # self.inputQueue = inputqueue
        ###############################################
        #### distance matrices ########################
        self.D = np.array(np.ones((self.pathLenMax, self.pathLenMax)) * np.inf)
        #this is a matrix of the cost of a path which terminates at point [x, y]
        #print(self.D)
        self.d = np.array(np.ones((self.pathLenMax, self.pathLenMax)) * np.inf)
        self.d[0,0] = 0
        self.D[0,0] = self.d[0,0]
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
        self.needNewFrame = 1
        self.runCount = 0
        self.i = 0
        self.bStart = 0
        self.durs = []
        # self.cuelist = cuelist
        # self.startTimer()

    # @pyqtSlot()
    
    @pyqtSlot()
    def align(self):
        '''
        OnlineDTW.align(): using a modified version of the dynamic time warping
        algorithm, finds a path of best alignment between two sequences, one
        known and one partially known. As frames of the partially known sequence
        are fed into the function, the "cost" or difference between both
        sequences is calculated, and the algorithm decides which point is
        the optimal next point in the least cost path by choosing the point with
        the least cost. Cost is cumulative and the cost of the current point
        depends on the cost of previous points. previous points also determine
        the direction that the algorithm predicts the next least cost point will
        be.

        TODO: needs to emit current alignment point to a OSC signal generator
        so that signals can be sent to QLab based on current alignment point.
        '''
        #!!!!!!!!!!!please read!!!!!!!!!!!!!!!!!!!!
        #note: dixon's description of the algorithm has the input index as the
        #row index of the cost matrix and the score index as the column index. i
        #prefer to think of the score index as the y axis, so i use the score
        #index as the row index of the cost matrix and the input index as the
        #columnwise index.
        #
        #or:
        #self.globalCostMatrix[scoreindex][inputindex] == proper way to index
        #cost matrix, as i've written it.
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        if self.j < self.frameNumScore:
            aa = time.time()
            # logging.debug("J less than")
            #print(f'path online index is {self.pathOnlineIndex}')
            #print(f'score index (J) is {self.scoreindex}')
            # self.needNewFrame = 1
            if self.needNewFrame == 1: # and not self.inputQueue.empty():
                newChroma = self.chromaQueue.get()
                # if self.bStart == 0:
                #     if np.sum(newChroma) == 0:                           
                #         return
                #     else:
                #         logging.debug('Audio detected!\n')
                #         self.bStart = 1;                                         
                self.U[:,:-1] = self.U[:,1:]
                # print(f"{self.U[:,-1].shape} {newChroma.shape}")
                self.U[:,-1] = newChroma[:,0]
                # chromaBuffer(:,1:end-1) = chromaBuffer(:,2:end);
                # chromaBuffer(:,end) = chroma;
            

            self.needNewFrame = 0
            direction = self._getInc()
            # logging.debug(f"{direction}")
            # IF GetInc(t,j) != Row
            #     j := j + 1
            #     FOR k := t - c + 1 TO t
            #         IF k > 0
            #             EvaluatePathCost(k,j)
            if direction in ["R","B"]:
                self.j += 1
                tt = np.max([0, self.t - self.c])
                ll = len(range(tt,self.t+1))
                assert ll == self.t+1-tt
                # TODO check the line below
                # logging.warning(f"{self.V.shape}")
                for k in range(tt, self.t+1):
                    self.d[self.j, k] = np.linalg.norm(self.V[:,self.j] - self.U[:,k-self.t+self.c-1])
                self.D[self.j, tt] = self.D[self.j-1, tt] + self.d[self.j, tt]
                for k in range(tt+1, self.t+1):
                    tmp1 = self.d[self.j, k] + self.D[self.j, k-1]
                    tmp2 = 0.5*self.d[self.j, k] + self.D[self.j-1, k-1]
                    tmp3 = self.d[self.j, k] + self.D[self.j-1, k]
                    self.D[self.j, k] = np.min([tmp1, tmp2, tmp3])

            if direction in ["C","B"]:
                self.t += 1
                self.needNewFrame = 1
                jj = np.max([0, self.j - self.c])
                ll = len(range(jj,self.j+1))
                assert ll == self.j+1-jj
                # TODO check the line below
                for k in range(jj, self.j+1):
                    self.d[k, self.t] = np.linalg.norm(self.V[:,k] - self.U[:,self.c-1])
                self.D[jj, self.t] = self.D[jj, self.t-1] + self.d[jj, self.t]
                for k in range(jj+1, self.j):
                    tmp1 = self.d[k, self.t] + self.D[k-1, self.t]
                    tmp2 = 0.5*self.d[k, self.t] + self.D[k-1, self.t-1]
                    tmp3 = self.d[k, self.t] + self.D[k, self.t-1]
                    self.D[k, self.t] = np.min([tmp1, tmp2, tmp3])


            if direction == self.previous:
                self.runCount = self.runCount + 1
            else:
                self.runCount = 1
            
            if direction != "B":
                self.previous = direction

            self.i += 1
            self.pathOnline[self.i,:] = [self.x, self.y]
            self.pathFront[self.i,:] = [self.t, self.j]
            # print(self.j)
            # self.signalToOSCclient.emit(self.i)
            if self.i % 50==0:
                self.signalToGUIThread.emit([self.x, self.y])
                self.signalToOSCclient.emit(self.i)
            self.durs.append(time.time() - aa)
        else:
            self.signalEnd.emit()
           
            
    ##get direction ##################################
    ##################################################
    def _getInc(self):
        '''
        _getInc: takes input index, score index as arguments and returns a
        char where:
        B = both
        C = column
        R = row
        which indicates the direction of the next alignment point
        '''

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
        tmp1 = self.D[self.j, :self.t+1]
        tt = np.arange(len(tmp1))
        tmp1 = tmp1 / np.sqrt(self.j**2+np.power(tt+1,2))

        tmp2 = self.D[:self.j+1, self.t]
        jj = np.arange(len(tmp2))
        tmp2 = tmp2 / np.sqrt(np.power(jj+1,2)+self.t**2)
        # ! python code (java based)
        # tmp1 = self.D[self.j, :self.t]
        # tmp2 = self.D[:self.j, self.t]

        # TODO in matlab's code there is a normalization step.
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
        
        # ! in dixon's paper the next 2 ifs are at the beggining of the 
        # ! function. In matlab's code they are at the end.
        if self.t < self.c:
            return "B"
        if self.runCount > self.maxRunCount:
            if self.previous == "R":
                return "C"
            else:
                return "R"

        if self.x < self.t:
            return "R"
        elif self.y < self.j:
            return "C"
        else:
            return "B"
        