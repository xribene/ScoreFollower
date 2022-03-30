import logging
from syslog import LOG_WARNING
from PyQt5.QtCore import (QObject, pyqtSignal, QTimer, pyqtSlot, QTimer
                           )
import numpy as np
import queue
from math import sqrt
import time
import pdb; 

class Aligner(QObject):
    signalToMainThread = pyqtSignal(object)
    signalEnd = pyqtSignal()
    def __init__(self, referenceChromas, chromaBuffer, n_chroma = 12, 
                        c = 200, maxRunCount = 3, 
                        metric = "sqeuclidean", w = 0.5):
        QObject.__init__(self)
        #### parameters ###############################
        self.c = c #  
        self.maxRunCount = maxRunCount
        self.metric = metric
        self.previous = None
        self.n_chroma = n_chroma
        self.referenceChromas = referenceChromas
        self.chromaQueue = chromaBuffer
        self.w = w
        self.j_todo = 0
        self.j_todo_flag = False
        ##############################################
        # self.scoreChroma = score_chroma
        self.lastChroma = np.zeros((n_chroma,1))
        self.zeroChroma = np.zeros((n_chroma,1))

        self.running = False
        self.reachedEnd = False
        self.recording = False
        self.pathOverflow = False
        self.reset()
        self.resetActivated = False # TODO prone to errors. The order shouldn't matter

    @pyqtSlot()
    def reset(self):
        self.resetActivated = True
        self.frameNumScore = self.referenceChromas.shape[0]
        self.frameNum = self.referenceChromas.shape[0]

        self.framenumaudio = self.frameNumScore # * 2 # in matlab code they use self.c

        self.pathLenMax = self.frameNumScore + self.framenumaudio
        self.V = np.transpose(self.referenceChromas)
        self.j = 0
        
        self.U = np.zeros((self.n_chroma, self.c)) # audio chromas
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
        self.durs = []
        self.chromaQueue.queue.clear()
        if self.reachedEnd is True:
            self.reachedEnd = False
            # self.align() # this is wrong. blocks UI

    @pyqtSlot()
    def align(self):
        logging.debug(f"MESAAAAAAAAAAAAA {self.j} {self.frameNumScore-1}")
        self.running = True
        while(self.j < self.frameNumScore-1 and self.resetActivated is False):
            
            if self.recording is True:
                aa = time.time()
                
                # logging.debug(f"before \n{self.D[:10,:10]}")
                if self.needNewFrame == 1: # and not self.inputQueue.empty():
                    try:
                        newChroma = self.chromaQueue.get(timeout=1)
                        self.lastChroma = newChroma
                    except:
                        if self.recording is True:
                            raise
                            # print("UNDERUN EMPTY QUEUE")
                            # newChroma = self.lastChroma
                        else:
                            continue
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

                if direction in ["C","B"]:
                    self.t += 1
                    self.needNewFrame = 1
                    jj = np.max([self.startFrameJ, self.j - self.c+1])
                    # ll = len(range(jj,self.j+1))
                    # assert ll == self.j+1-jj
                    for k in range(jj, self.j+1):
                        self.d[k, self.t] = np.linalg.norm(self.V[:,k] - self.U[:,-1])**2
                    self.D[jj, self.t] = self.D[jj, self.t-1] + self.d[jj, self.t]
                    for k in range(jj+1, self.j+1):
                        tmp1 = self.d[k, self.t] + self.D[k-1, self.t]
                        tmp2 = self.w*self.d[k, self.t] + self.D[k-1, self.t-1]
                        tmp3 = self.d[k, self.t] + self.D[k, self.t-1]
                        self.D[k, self.t] = np.min([tmp1, tmp2, tmp3])
                        if not np.isfinite(np.min([tmp1, tmp2, tmp3])).all():
                            logging.error(f'inf in T calc')
                            raise

                if direction in ["R","B"]:
                    self.j += 1
                    tt = np.max([self.startFrameT, self.t - self.c + 1])
                    # ll = len(range(tt,self.t+1))
                    # assert ll == self.t+1-tt
                    for k in range(tt, self.t+1):
                        self.d[self.j, k] = np.linalg.norm(self.V[:,self.j] - self.U[:,k-self.t+self.c-1])**2
                    self.D[self.j, tt] = self.D[self.j-1, tt] + self.d[self.j, tt]
                    for k in range(tt+1, self.t+1):
                        tmp1 = self.d[self.j, k] + self.D[self.j, k-1]
                        tmp2 = self.w*self.d[self.j, k] + self.D[self.j-1, k-1]
                        tmp3 = self.d[self.j, k] + self.D[self.j-1, k]
                        self.D[self.j, k] = np.min([tmp1, tmp2, tmp3])
                        if not np.isfinite(np.min([tmp1, tmp2, tmp3])).all():
                            logging.error(f'inf in J calc')
                            raise
                            
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
                # print(self.j)
                # self.signalToOSCclient.emit(self.i)
                
                self.signalToMainThread.emit([self.t, self.j])
                self.durs.append(time.time() - aa)
            else:  
                # print(f"{self.recording}")
                time.sleep(0.1)
                # pass

        if self.j == self.frameNumScore-1:
            self.reachedEnd = True
            self.signalEnd.emit()
            logging.debug(f"reached END - END OF WHILE")
        if self.resetActivated is True:
            logging.debug(f"End of While because RESET 1")
            self.resetActivated = False
            logging.debug(f"set resetActivated to False")
        if self.pathOverflow is True:
            self.pathOverflow = False
            self.signalEnd.emit()
            logging.debug(f"end of while - OVERFLOW")
            # pass
            # self.reachedEnd = True
            # self.signalEnd.emit()
        self.running = False
            
    # @pyqtSlot(int)     
    # def setStartingScoreFrame(self, frame):
    #     if self.running:
    #         if frame < self.j:
    #             self.j_todo = frame
    #             self.j_todo_flag = True
    #     else:
    #         self.j = frame
    #         logging.debug(f'not running --> set self.j={frame}')
            
        # self.j = frame    
        # if isStopped tote to self.j einai safe na ginei apo 0 ws maxScoreFrame
        # if running tote to self.j einai safe na paei pisw. 
        # i.e if self.j = 300 and frame 305  
    ##get direction ##################################
    ##################################################
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
        
        # if self.t < self.c:
        #     return "B"
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