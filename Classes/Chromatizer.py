from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot)
from scipy import ndimage
from librosa import feature, display, decompose
import logging
import numpy as np
import librosa
from scipy.fft import rfft

class Chromatizer(QObject):
    def __init__(self, chromaBuffer, rate = 44100, 
                        chromaType = 'stft', hop_length = 1024, 
                        window_length = 2048,
                        n_fft = 8192, n_chroma = 12,
                        norm=2, normAudio = False, 
                        windowType='hann', 
                        chromafb = None, magPower = 1, 
                        defaultRmsThr = 0.0, lowestFreq = 100):
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
        self.lastChroma = np.ones((n_chroma,1)) / np.sqrt(n_chroma)
        self.zeroChroma = np.zeros((n_chroma,1)) / np.sqrt(n_chroma)
        self.rmsThr = defaultRmsThr
        self.fft_window = librosa.filters.get_window(windowType, window_length, fftbins=True)
        self.fft_freqs = librosa.core.fft_frequencies(sr = self.rate, n_fft = self.n_fft)
        self.lowestFreq = lowestFreq
        self.lowestBin = np.where(self.fft_freqs <= self.lowestFreq)[0][-1]
        # np.save("fftWindow.npy", self.fft_window)
        self.n_chroma = n_chroma
        self.tuning = 0.0
        #%%
        if chromafb:
            self.chromafb = chromafb
        else:
            self.chromafb = librosa.filters.chroma(sr = rate, n_fft = n_fft, tuning=0.0, n_chroma=n_chroma)
            self.chromafb[:,:self.lowestBin] = 0

    @pyqtSlot(object)
    def setLowestFreq(self, newFreq):
        self.lowestFreq = newFreq
        self.lowestBin = np.where(self.fft_freqs <= self.lowestFreq)[0][-1]

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
            if rms >= self.rmsThr:
                chunk_win = self.fft_window * y_conc
                real_fft = rfft(chunk_win, n = self.n_fft)
                fft_mag = np.abs(real_fft)**self.magPower
                # shape=(d, t)]
                # self.tuning = librosa.pitch.estimate_tuning(S=fft_mag.reshape(-1,1), sr=self.rate, bins_per_octave=self.n_chroma)
                # self.chromafb = librosa.filters.chroma(sr = self.rate, n_fft = self.n_fft, tuning=self.tuning, n_chroma=self.n_chroma)
                self.chromafb[:,:self.lowestBin] = 0
                raw_chroma = np.dot(self.chromafb, fft_mag)
                norm_chroma = librosa.util.normalize(raw_chroma, norm=self.norm, axis=0).reshape(-1,1)
                # logging.debug(f"norm Chroma shape is {norm_chroma.shape}")
                # chromaFrames.append(norm_chroma)
                # print(f"chroma {np.transpose(norm_chroma)}")
            else:
                norm_chroma = self.zeroChroma
                # print(f"zero chroma {np.transpose(norm_chroma)}")
            # self.chromasList.append(norm_chroma)
            self.chromaBuffer.put_nowait(norm_chroma)
            # self.signalToOnlineDTW.emit(chroma)
        # ! no need for that. Aligner can take the queue as input argument
        # @pyqtSlot()
        # def getLastChroma(self):
        #     return self.outputqueue.get_nowait()