from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot)
from scipy import ndimage
from librosa import feature, display, decompose
import logging
import numpy as np
import librosa
from scipy.fft import rfft


class Chromatizer(QObject):
    '''
    Chromatizer(QObject): accepts chunks of audio information as input
    from audio buffer, calculates chroma matrix of audio chunk,
    pushes chroma information to chroma queue for comparison to
    reference chroma. Currently prints value of fundamental frequency
    of audio chunk.
    '''
    signalToOnlineDTW = pyqtSignal(object)
    def __init__(self, chromaBuffer, rate = 22050, 
                        chromaType = 'stft', hop_length = 1024, window_length = 2048,
                        n_fft = 4096, n_chroma = 12):
        QObject.__init__(self)
        self.chromaBuffer = chromaBuffer
        self.rate = rate
        self.hop_length = hop_length
        self.window_length = window_length
        self.n_fft = n_fft
        self.chromaType = chromaType
        # TODO win_len - hop_len is not the correct formula here. It only works for 50% overlap
        self.buffer = np.zeros(window_length - hop_length).astype(np.float32)
        self.chromasList = []
        self.lastChroma = np.zeros((n_chroma,1))
        self.fft_window = librosa.filters.get_window("hann", window_length, fftbins=True)
        self.n_chroma = n_chroma
        #%%
        self.chromafb = librosa.filters.chroma(sr = rate, n_fft = n_fft, tuning=0.0, n_chroma=n_chroma)


    # def _display(self):
    #     chroma = self.chroma_frames.get_nowait()
    #     display.specshow(chroma, y_axis = "chroma", x_axis = "time")

    @pyqtSlot(object)
    def calculate(self, frame):
        # frame is expected to have size = hop_length
        # logging.debug(f"frame max {max(frame)} min {min(frame)}")
        y = frame.astype('float32') / 32768.0
        y_conc = np.concatenate((self.buffer, y))
        # logging.debug(f"{self.buffer.shape} {y.shape} {y_conc.shape}")
        self.buffer = y_conc[self.hop_length:]

        # mag = np.linalg.norm(y_conc)
        power = np.mean(np.abs(y_conc) ** 2, axis=0, keepdims=True)
        rms = np.sqrt(power)
        # logging.debug(f"{np.min(frame)} {np.max(frame)} {frame.dtype}")
        # logging.debug(f"{self.chromaBuffer.qsize()}")
        #
        # TODO check java and matlab code, use rms
        if rms > -0.01:
            # if self.chromaType == 'cqt':
            #     chroma = feature.chroma_cqt(y_conc, sr = self.rate,
            #                                 hop_length = self.hop_length,
            #                                bins_per_octave = 12*3)[:,1:2]
            #                                # ! use the middle vector ? 
            # elif self.chromaType == 'stft': 
                
            # chroma = feature.chroma_stft(y_conc, sr = self.rate,
            #                             n_fft = self.n_fft,
            #                             hop_length = self.hop_length
            #                             )
            # logging.debug(f"chroma shape {chroma.shape}")
            # chroma = chroma[:,1:2]
            # chunk = wav[i*stride:i*stride+frame_len]
            chunk_win = self.fft_window * y_conc
            real_fft = rfft(chunk_win, n = self.n_fft)
            fft_mag = np.abs(real_fft)**2
            raw_chroma = np.dot(self.chromafb, fft_mag)
            norm_chroma = librosa.util.normalize(raw_chroma, norm=np.inf, axis=0).reshape(-1,1)
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
