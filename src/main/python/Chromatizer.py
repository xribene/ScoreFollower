from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot)
from scipy import ndimage
from librosa import feature, display, decompose
import logging
import numpy as np
import librosa
from scipy.fft import rfft
from offline.utils_offline import get_window, librosaFiltersChroma, librosaNormalize

class Chromatizer(QObject):
    signalToOnlineDTW = pyqtSignal(object)
    def __init__(self, chromaBuffer, rate = 44100, 
                        chromaType = 'stft', hop_length = 1024, 
                        window_length = 2048,
                        n_fft = 8192, n_chroma = 12,
                        norm=2, normAudio = False, 
                        windowType='hann',
                        chromafb = None, magPower = 1):
        QObject.__init__(self)
        self.chromaBuffer = chromaBuffer
        self.rate = rate
        self.hop_length = hop_length
        self.window_length = window_length
        self.n_fft = n_fft
        self.chromaType = chromaType
        self.magPower =  magPower
        self.normAudio = normAudio
        self.norm = norm
        # TODO win_len - hop_len is not the correct formula here. It only works for 50% overlap
        self.buffer = np.zeros(window_length - hop_length).astype(np.float32)
        self.chromasList = []
        self.lastChroma = np.zeros((n_chroma,1))
        self.fft_window = get_window(windowType, window_length, fftbins=True)
        # np.save("fftWindow.npy", self.fft_window)
        self.n_chroma = n_chroma
        #%%
        if chromafb:
            self.chromafb = chromafb
        else:
            self.chromafb = librosaFiltersChroma(sr = rate, n_fft = n_fft, tuning=0.0, n_chroma=n_chroma)
            # np.save("chromafbLibrosa.npy",self.chromafb)

    @pyqtSlot(object)
    def calculate(self, frame):
        # frame is expected to have size = hop_length
        # logging.debug(f"frame max {max(frame)} min {min(frame)}")
        y = frame.astype('float32') / 32768.0
        y_conc = np.concatenate((self.buffer, y))
        if y_conc.shape[0] == self.window_length:
            # logging.debug(f"{self.buffer.shape} {y.shape} {y_conc.shape}")
            self.buffer = y_conc[self.hop_length:]

            # mag = np.linalg.norm(y_conc)
            power = np.mean(np.abs(y_conc) ** 2, axis=0, keepdims=True)
            rms = np.sqrt(power)
            # logging.debug(f"{np.min(frame)} {np.max(frame)} {frame.dtype}")
            # logging.debug(f"{self.chromaBuffer.qsize()}")
            #
            # TODO see what to do with the threshold here
            if rms > -0.01:
                chunk_win = self.fft_window * y_conc
                real_fft = rfft(chunk_win, n = self.n_fft)
                fft_mag = np.abs(real_fft)**self.magPower
                raw_chroma = np.dot(self.chromafb, fft_mag)
                norm_chroma = librosaNormalize(raw_chroma, norm=self.norm, axis=0).reshape(-1,1)
                # logging.debug(f"norm Chroma shape is {norm_chroma.shape}")
                # chromaFrames.append(norm_chroma)
            else:
                norm_chroma = self.lastChroma
            # logging.debug(f"{chroma[:,0].astype(np.int)}")
            self.chromasList.append(norm_chroma)
            self.chromaBuffer.put_nowait(norm_chroma)
            # self.signalToOnlineDTW.emit(chroma)
        # ! no need for that. Aligner can take the queue as input argument
        # @pyqtSlot()
        # def getLastChroma(self):
        #     return self.outputqueue.get_nowait()