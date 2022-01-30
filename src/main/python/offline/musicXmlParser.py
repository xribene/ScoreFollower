#%%
from librosa.core.audio import BW_BEST
import music21
from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt
import librosa
import librosa.display
from tslearn.metrics.dtw_variants import cdist_dtw

#%%
def circConv(a,b):
    n = a.shape[0]
    return np.convolve(np.tile(a, 2), b)[n:2 * n]

#%%
fileName = Path("jetee4.mid")
wav, sr = librosa.load('jetee.wav', sr = 44100)#, duration=15)
# fileName = Path("wtq.mid")
# wav, sr = librosa.load('wtq2.wav', sr = 44100)#, duration=15)
print(f"wav duration {wav.shape[0]/sr}")
score = music21.converter.parse(fileName)
#%%
scoreTree = score.asTimespans()
scoreTreeNotes = score.asTimespans(classList=(music21.note.Note,music21.note.Rest, music21.chord.Chord))
#%%

# tempo = score[music21.tempo.MetronomeMark][0]
tempo = score.recurse().getElementsByClass(music21.tempo.MetronomeMark)[0]

secsPerQuarter = tempo.secondsPerQuarter()

# timeSign = score[music21.meter.TimeSignature][0]
timeSign = score.recurse().getElementsByClass(music21.meter.TimeSignature)[0]
secsPerSixteenth = secsPerQuarter / 4
scoreDurQuarter = score.duration.quarterLength
print(f"score duration {secsPerQuarter*scoreDurQuarter}")
# quantities for chroma calculation.
chromaFrameSeconds = 0.04643#secsPerSixteenth #  0.046
chromaFrameQuarters = chromaFrameSeconds / secsPerQuarter
chromaFramesNum = int(scoreDurQuarter/chromaFrameQuarters)
measureFramesNum =  int(timeSign.barDuration.quarterLength / chromaFrameQuarters)

#%%
notesHist = np.zeros((chromaFramesNum, 12))
chromagram = np.zeros_like(notesHist)
# start = 0.0
# end = start + chromaFrameQuarters

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
        notesHist[startInd:endInd, x] += 1 
#%%
# 1+1/2 + 1/9 Nto  
# sol 1/4 + 1/25
# mi 1/16
# siB 1/36
# C C G C E G Bb
# 1^2 2^2 3^2
harmonicTemplate = np.array([1+1/4+1/16,0,0,0,1/25,0,0,1/9+1/36,0,0,1/49,0])
# harmonicTemplate = np.array([1+1/2,0,0,0,0,0,0,1/4,0,0,1/16,0])
for i in range(chromaFramesNum):
    chromagram[i] = circConv(harmonicTemplate, notesHist[i])
    if np.max(chromagram[i]) != 0 : 
        # print(chromagram[i])
        chromagram[i] = chromagram[i] / np.max(chromagram[i])
    else:
        print(i)

#%%

n_fft = 4096 #int(sr * chromaFrameSeconds) 
hop_length = n_fft //2
chromaWavStft = librosa.feature.chroma_stft(y=wav, sr=sr, n_fft=n_fft, hop_length = hop_length)
chromaWavCqt = librosa.feature.chroma_cqt(y=wav, sr=sr, hop_length=hop_length)

print(chromaWavStft.shape)
# %%
# aaa = 1841
# bbb = aaa + 200

# fig, ax = plt.subplots()
# img = librosa.display.specshow(chromaWavCqt[:,0:3], hop_length = 2205, y_axis='chroma', x_axis='time', ax=ax)
# fig.colorbar(img, ax=ax)
# ax.set(title='ChromagramWav')

# fig, ax = plt.subplots()
# img = librosa.display.specshow(np.transpose(chromagram[aaa:bbb,:]), hop_length = 2205,y_axis='chroma', x_axis='time', ax=ax)
# fig.colorbar(img, ax=ax)
# ax.set(title='ChromagramScore')
# %%
from tslearn.metrics import dtw, dtw_path
from scipy.spatial.distance import cdist

# dtw_score = dtw(x, y)
x = np.transpose(chromaWavStft)
y = chromagram
z = np.load("recordedChromas.npy")
path, dtw_score = dtw_path(x,y)
mat = cdist(x,y)

plt.figure(1, figsize=(8, 8))

left, bottom = 0.01, 0.1
w_ts = h_ts = 0.2
left_h = left + w_ts + 0.02
width = height = 1.65
bottom_h = bottom + height + 0.02

rect_gram = [left_h, bottom, width, height]

ax_gram = plt.axes()

ax_gram.imshow(mat, origin='lower')
ax_gram.plot([j for (i, j) in path], [i for (i, j) in path], "b-",
             linewidth=3.)

print(dtw_score)
plt.tight_layout()
plt.show()
# %%
