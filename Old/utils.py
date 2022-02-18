import numpy as np
import music21
from pathlib import Path
from matplotlib import pyplot as plt
import librosa
import librosa.display
import json
import logging
from scipy.fft import rfft

def circConv(a,b):
    n = a.shape[0]
    return np.convolve(np.tile(a, 2), b)[n:2 * n]

def getReferenceChromas(filePath, sr = 44100, n_fft = 4096, window_length = 2048,
                        hop_length = 1024, chromaType = "stft", n_chroma = 12,
                        norm=np.inf, normAudio = False, windowType='hann',
                        chromafb = None, magPower = 1):
    # TODO if the folders exist, don't generate chromas again.
    
    ext = str(filePath.parts[-1]).split(".")[-1]
    # logging.info(f'{ext}')
    if ext in ["xml","mid"]:
        print(filePath)

        score = music21.converter.parse(filePath)
        scoreTree = score.asTimespans()
        scoreTreeNotes = score.asTimespans(classList=(music21.note.Note,music21.note.Rest, music21.chord.Chord))

        # find tempo and time signature info

        # tempo = score[music21.tempo.MetronomeMark][0]
        tempo = score.recurse().getElementsByClass(music21.tempo.MetronomeMark)[0]

        secsPerQuarter = tempo.secondsPerQuarter()

        # timeSign = score[music21.meter.TimeSignature][0]
        timeSign = score.recurse().getElementsByClass(music21.meter.TimeSignature)[0]
        secsPerSixteenth = secsPerQuarter / 4
        scoreDurQuarter = score.duration.quarterLength
        # print(f"score duration {secsPerQuarter*scoreDurQuarter}")
        # quantities for chroma calculation.
        chromaFrameSeconds = hop_length/sr #secsPerSixteenth #  0.046
        chromaFrameQuarters = chromaFrameSeconds / secsPerQuarter
        chromaFramesNum = int(scoreDurQuarter/chromaFrameQuarters)
        measureFramesNum =  int(timeSign.barDuration.quarterLength / chromaFrameQuarters)

        #
        notesHist = np.zeros((chromaFramesNum, n_chroma))
        chromagram = np.zeros_like(notesHist)

        for vert in scoreTreeNotes.iterateVerticalities():
            startInd = int(np.ceil(vert.offset / chromaFrameQuarters))
            nextOffset = scoreTreeNotes.getPositionAfter(vert.offset)
            if nextOffset is None:
                nextOffset = scoreDurQuarter
            endInd = int(np.ceil(nextOffset / chromaFrameQuarters))

            # notesHist[:,startInd:endInd]
            chord = vert.toChord()
            pitchClasses = chord.pitchClasses
            for x in pitchClasses:
                notesHist[startInd:endInd, x] = 1 
        #%%
        harmonicTemplate = np.array([1+1/4+1/16,0,0,0,1/25,0,0,1/9+1/36,0,0,1/49,0])
        for i in range(chromaFramesNum):
            chromagram[i] = circConv(harmonicTemplate, notesHist[i])
            if np.max(chromagram[i]) != 0 : 
                # print(chromagram[i])
                # chromagram[i] = chromagram[i] / np.max(chromagram[i])
                chromagram[i] = librosa.util.normalize(chromagram[i], norm=norm, axis=0)
            else:
                print(i)
    elif ext == "wav":
        wav, sr = librosa.load(filePath, sr = sr)#, duration=15)
        if normAudio is True:
            wav = wav/np.sqrt(np.mean(wav**2))
        if chromaType == "cqt":
            chromagram = librosa.feature.chroma_cqt(y=wav, sr=sr, hop_length=hop_length)
        elif chromaType == "stft":
            # chromagram = librosa.feature.chroma_stft(y=wav, sr=sr, n_fft = n_fft, 
            #                                             hop_length=hop_length)
            # chromagram = np.transpose(chromagram)
            #%%
            stftFrames = []
            chromaFrames = []
            i = 0
            fft_window = librosa.filters.get_window(windowType, window_length, fftbins=True)
            tuning = 0.0 #librosa.core.pitch.estimate_tuning(y=wav, sr=sr, bins_per_octave=n_chroma)
            if chromafb is None:
                chromafb = librosa.filters.chroma(sr, n_fft, tuning=tuning, n_chroma=n_chroma)

            stride = hop_length
            frame_len = window_length
            # y_frames = librosa.util.frame(wav, frame_length=n_fft, hop_length=hop_length)
            #
            ## What I think is right, and also matches with matlab
            while i*stride+frame_len < wav.shape[-1]:
                chunk = wav[i*stride:i*stride+frame_len]
                chunk_win = fft_window * chunk
                real_fft = rfft(chunk_win, n = n_fft)
                stftFrames.append( np.abs(real_fft)** magPower )
                raw_chroma = np.dot(chromafb, stftFrames[-1])
                norm_chroma = librosa.util.normalize(raw_chroma, norm=norm, axis=0)
                chromaFrames.append(norm_chroma)

                i += 1

            chromagram = np.array(chromaFrames)
   
        # print(chromaWav.shape)
        # print(f"wav duration {wav.shape[0]/sr}")
    return chromagram  


class Params():
    """Class that loads hyperparameters from a json file.
    Example:
    ```
    params = Params(json_path)
    print(params.learning_rate)
    params.learning_rate = 0.5  # change the value of learning_rate in params
    ```
    """

    def __init__(self, json_path):
        with open(json_path) as f:
            params = json.load(f)
            self.__dict__.update(params)

    def save(self, json_path):
        with open(json_path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

    def update(self, json_path):
        """Loads parameters from json file"""
        with open(json_path) as f:
            params = json.load(f)
            self.__dict__.update(params)

    @property
    def dict(self):
        """Gives dict-like access to Params instance by `params.dict['learning_rate']"""
        return self.__dict__


