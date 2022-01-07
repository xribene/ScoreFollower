from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot)
from scipy import ndimage
from librosa import feature, display, decompose
import logging
import numpy as np

class Chromatizer(QObject):
    '''
    Chromatizer(QObject): accepts chunks of audio information as input
    from audio buffer, calculates chroma matrix of audio chunk,
    pushes chroma information to chroma queue for comparison to
    reference chroma. Currently prints value of fundamental frequency
    of audio chunk.
    '''
    signalToOnlineDTW = pyqtSignal(object)
    def __init__(self, inputqueue, outputqueue, rate = 22050, 
                        chromaType = 'cqt', hop_length = 1024,
                        n_fft = 2048):
        QObject.__init__(self)
        self.outputqueue = outputqueue
        self.inputqueue = inputqueue
        self.rate = rate
        self.hop_length = hop_length
        self.n_fft = n_fft
        self.chromaType = chromaType
        self.buffer = np.zeros(n_fft - hop_length).astype(np.float32)
        self.chromasList = []
    def _display(self):
        chroma = self.chroma_frames.get_nowait()
        display.specshow(chroma, y_axis = "chroma", x_axis = "time")

    @pyqtSlot(object)
    def calculate(self, frame):
        # frame is expected to have size = hop_length
        y = frame.astype('float32') / 32768.0
        y_conc = np.concatenate((self.buffer, y))
        # logging.debug(f"{self.buffer.shape} {y.shape} {y_conc.shape}")
        self.buffer = y_conc[self.hop_length:]

        mag = np.linalg.norm(y_conc)
        power = np.mean(np.abs(y_conc) ** 2, axis=0, keepdims=True)
        mag2 = np.sqrt(power)
        # logging.debug(f"{np.min(frame)} {np.max(frame)} {frame.dtype}")
        # logging.debug(f"{mag} {mag2}")
        #
        # TODO check java and matlab code, use rms
        if mag > 0:
            if self.chromaType == 'cqt':
                chroma = feature.chroma_cqt(y_conc, sr = self.rate,
                                            hop_length = self.hop_length,
                                           bins_per_octave = 12*3)[:,1:2]
                                           # ! use the middle vector ? 
            elif self.chromaType == 'stft': 
                
                chroma = feature.chroma_stft(y_conc, sr = self.rate,
                                            n_fft = self.n_fft,
                                            hop_length = self.hop_length
                                           )[:,0:1]
                # logging.debug(f"in stft {chroma}")
            #filtering reduces volume of noise/partials
            # chroma_filtered = np.minimum(chroma,
            #                                 decompose.nn_filter(chroma,
            #                                 aggregate = np.median,
            #                                 metric = 'cosine'))
            # chroma_smooth = ndimage.median_filter(chroma_filtered,
            #                                         size = (1,9))
            # np.place(chroma_smooth, np.isnan(chroma_smooth), [0])
            # chroma_smooth = np.mean(chroma_smooth, axis = 1)
        else:
            chroma = np.array([[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0]])
        self.chromasList.append(chroma)
        # self.outputqueue.put_nowait(chroma_smooth)
        self.signalToOnlineDTW.emit(chroma)
