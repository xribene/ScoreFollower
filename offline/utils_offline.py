import numpy as np
import music21
from pathlib import Path
from matplotlib import pyplot as plt
import librosa
import librosa.display
import json
import logging
from scipy.fft import rfft
from scipy import signal

import scipy.io as sio
from collections import OrderedDict, defaultdict
import sys, os
def circConv(a,b):
    n = a.shape[0]
    return np.convolve(np.tile(a, 2), b)[n:2 * n]
class OrderedDictDefaultList(OrderedDict):
    def __missing__(self, key):
        value = list()
        self[key] = value
        return value
def chromaFilterbanks(type = "librosa", n_fft = 8192, sr = 44100, n_chroma = 12, 
                        tuning = 0, base_c = True, extend = 0.1):
    if type == "librosa":
        fb = librosa.filters.chroma(sr, n_fft, tuning=tuning, n_chroma=n_chroma)
    elif type == "bochen":
        if n_fft != 8192 or sr != 44100 or n_chroma != 12 or tuning != 0:
            raise
        fb = sio.loadmat("/home/xribene/Projects/code_matlab_2019/F2CM.mat")['F2CM']#,mat_dtype =np.float32)
        if base_c is True:
            # TODO np.roll
            pass
    elif type == "mine":
        fb = np.zeros((n_chroma, n_fft//2+1))
        fb88 = np.zeros((88, n_fft//2+1))
        # frequencies = librosa.fft_frequencies(sr,n_fft)
        prevFreq = librosa.midi_to_hz(20)
        prevBin =  int((n_fft//2)*prevFreq / (sr/2))

        nextFreq = librosa.midi_to_hz(21)
        nextBin =  int((n_fft//2)*nextFreq / (sr/2))
        for i, midi in enumerate(range(21,109)):
            # currentFreq = nextFreq
            # currentBin = nextBin

            nextFreq =  librosa.midi_to_hz(midi+1)
            nextBin = int((n_fft//2)*nextFreq / (sr/2))

            samples = 2*((nextBin - prevBin)//2) + 1
            filter = createFrequencyBP(type = "gaussian", samples = samples, extend = extend)
            fb88[i, prevBin:(prevBin+samples) ] = filter

        # def midi_to_hz(notes):
        # def hz_to_midi(frequencies):
        # def midi_to_note(midi, octave=True, cents=False, key="C:maj", unicode=True):
        # def note_to_midi(note, round_midi=True):


    return fb88

def createFrequencyBP(type='triangular', samples = 10, extend = 0.1):
    if type == "trianglar":
        bp = signal.windows.triang(samples)
    elif type == "gaussian":
        bp = signal.windows.gaussian(samples, std = samples*extend, sym=True)
    return bp

def getCuesDict(filePath, sr = 44100, hop_length = 1024):
    score = music21.converter.parse(filePath)
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

    cuesPart = next(part for part in score.parts if part.partName=="CUES")
    cues = list(cuesPart.recurse().getElementsByClass(music21.expressions.RehearsalMark))
    measureMap = cuesPart.measureOffsetMap()

    frame2CueDict = defaultdict(list)#OrderedDictDefaultList()
    for i, cue in enumerate(cues):
        currentFrame = int(np.ceil(cue.getOffsetInHierarchy(score) / chromaFrameQuarters))
        frame2CueDict[currentFrame].append({"type":"cue","ind":i,"name":cue.content})

    for off, m in measureMap.items():
        currentFrame = int(np.ceil(off / chromaFrameQuarters))
        frame2CueDict[currentFrame].append({"type":"bar","ind":m[0].number})
    return dict(frame2CueDict)

def getChromas(filePath, sr = 44100, n_fft = 8192, window_length = 2048,
                        hop_length = 1024, chromaType = "stft", n_chroma = 12,
                        norm=2, normAudio = False, windowType='hamming',
                        chromafb = None, magPower = 1):
    # TODO if the folders exist, don't generate chromas again.
    ext = str(filePath.parts[-1]).split(".")[-1]
    # logging.info(f'{ext}')
    if ext in ["xml","mid"]:
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
        notesHist = np.zeros((n_chroma, chromaFramesNum))
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
                notesHist[x, startInd:endInd] += 1 
        #%%
        harmonicTemplate = np.array([1+1/4+1/16,0,0,0,1/25,0,0,1/9+1/36,0,0,1/49,0])
        for i in range(chromaFramesNum):
            chromagram[:,i] = circConv(harmonicTemplate, notesHist[:,i])
            if np.max(chromagram[:,i]) != 0 : 
                # print(chromagram[i])
                # chromagram[i] = chromagram[i] / np.max(chromagram[i])
                chromagram[:,i] = librosa.util.normalize(chromagram[:,i], norm=norm, axis=0)
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
                # norm_chroma = librosa.util.normalize(raw_chroma, norm=norm, axis=0)
                # 
                chromaVector = getChromaFrame(chunk = chunk, chromafb = chromafb, fft_window = fft_window, 
                                                n_fft = n_fft ,norm = norm, magPower = magPower)
                chromaFrames.append(chromaVector)
                i += 1

            chromagram = np.array(chromaFrames)
   
    return chromagram   

def getChromaFrame(chunk, chromafb, fft_window, n_fft = 4096,norm=2, magPower = 1):
    chunk_win = fft_window * chunk
    real_fft = rfft(chunk_win, n = n_fft)
    psd = np.abs(real_fft)** magPower
    raw_chroma = np.dot(chromafb, psd)
    norm_chroma = librosa.util.normalize(raw_chroma, norm=norm, axis=0)
    return norm_chroma

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


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def returnCorrectFile(path, ext):
    pieceName = path.parts[-2]
    sectionName = "".join(path.parts[-1].split("_")[1:])
    files = [f for f in path.iterdir() if f.is_file()]
    listOfFiles = [f for f in files if f.suffix == f'.{ext}']
    if (len(listOfFiles) == 0):
        print(f"No {ext} files detected in {path}")
        raise
    elif (len(listOfFiles) > 1):
        print(f"Multiple {ext} files found in {path}, expected to find only {pieceName}_{sectionName}.{ext}")
        raise
    elif (len(listOfFiles) == 1):
        assert (path/f"{pieceName}_{sectionName}.{ext}").is_file(), f"I was expected to find {pieceName}_{sectionName}.{ext} in {path}"
        correctFile = listOfFiles[0]
    return correctFile