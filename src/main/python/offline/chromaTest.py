#%%
from librosa.core.audio import BW_BEST
import music21
from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt
import librosa
import librosa.display
from tslearn.metrics.dtw_variants import cdist_dtw
from scipy.fft import fft, rfft     

#%%
wav, sr = librosa.load('jetee.wav', sr = 44100)#, duration=15)
print(f"wav duration {wav.shape[0]/sr}")
#%%
n_fft = 4096 #int(sr * chromaFrameSeconds) 
window_length = 2048
hop_length = window_length //2
n_chroma = 12
norm=np.inf
#%%
stftFrames = []
chromaFrames = []
i = 0
fft_window = librosa.filters.get_window("hann", window_length, fftbins=True)
fft_window_pad = librosa.util.pad_center(fft_window, n_fft)
# fft_window_pad = fft_window_pad.reshape((-1, 1))
tuning = 0.0 #librosa.core.pitch.estimate_tuning(y=wav, sr=sr, bins_per_octave=n_chroma)
chromafb = librosa.filters.chroma(sr, n_fft, tuning=tuning, n_chroma=n_chroma)

stride = hop_length
frame_len = n_fft
y_frames = librosa.util.frame(wav, frame_length=n_fft, hop_length=hop_length)


while i*stride+frame_len < wav.shape[-1]:
    chunk = wav[i*stride:i*stride+frame_len]
    chunk_win = fft_window_pad * chunk
    real_fft = rfft(chunk_win)
    stftFrames.append( np.abs(real_fft)** 2 )
    raw_chroma = np.dot(chromafb, stftFrames[-1])
    norm_chroma = librosa.util.normalize(raw_chroma, norm=norm, axis=0)
    chromaFrames.append(norm_chroma)

    i += 1
# for j in range(y_frames.shape[1]):
#     chunk = y_frames[:,i]
#     chunk_win = fft_window_pad * chunk
#     real_fft = rfft(chunk_win)
#     stftFrames.append( np.abs(real_fft)** 2 )
#     raw_chroma = np.dot(chromafb, stftFrames[-1])
#     norm_chroma = librosa.util.normalize(raw_chroma, norm=norm, axis=0)
#     chromaFrames.append(norm_chroma)
chromaFramesNp = np.array(chromaFrames)
plt.imshow(chromaFramesNp[:30])
#%%
chromaWavStft = np.transpose(librosa.feature.chroma_stft(y=wav, 
                                            sr=sr, 
                                            n_fft=2*n_fft, 
                                            hop_length = hop_length,
                                            # S=None,
                                            norm=np.inf,
                                            win_length=window_length,
                                            window="hann",
                                            center=False,
                                            pad_mode="reflect",
                                            tuning=0.0,
                                            n_chroma=12
    ))
print(chromaWavStft.shape)
plt.imshow(chromaWavStft[:30])

#%%
# %%
from tslearn.metrics import dtw, dtw_path
from scipy.spatial.distance import cdist

# dtw_score = dtw(x, y)
x = chromaWavStft
y = chromaFramesNp
z = np.load("recordedChromas_New.npy")
path, dtw_score = dtw_path(y,z)
mat = cdist(y,z)

plt.figure(1, figsize=(8, 8))

left, bottom = 0.01, 0.1
w_ts = h_ts = 0.2
left_h = left + w_ts + 0.02
width = height = 1.65
bottom_h = bottom + height + 0.02

rect_gram = [left_h, bottom, width, height]

ax_gram = plt.axes()

ax_gram.imshow(mat, origin='lower')
ax_gram.plot([j for (i, j) in path], [i for (i, j) in path], "r-",
             linewidth=3.)

print(dtw_score)
plt.tight_layout()
plt.show()


#%%
n_fft = 4096 #int(sr * chromaFrameSeconds) 
window_length = 2048
hop_length = window_length //2
n_chroma = 12
norm=np.inf
#%%
stftFrames = []
chromaFrames = []
i = 0
fft_window = librosa.filters.get_window("hann", window_length, fftbins=True)
# fft_window_pad = librosa.util.pad_center(fft_window, n_fft)
# fft_window_pad = fft_window_pad.reshape((-1, 1))
tuning = 0.0 #librosa.core.pitch.estimate_tuning(y=wav, sr=sr, bins_per_octave=n_chroma)
chromafb = librosa.filters.chroma(sr, n_fft, tuning=tuning, n_chroma=n_chroma)

stride = hop_length
frame_len = window_length
y_frames = librosa.util.frame(wav, frame_length=n_fft, hop_length=hop_length)
#
## What I think is right, and also matches with matlab
while i*stride+frame_len < wav.shape[-1]:
    chunk = wav[i*stride:i*stride+frame_len]
    chunk_win = fft_window * chunk
    real_fft = rfft(chunk_win, n = n_fft)
    stftFrames.append( np.abs(real_fft)** 2 )
    raw_chroma = np.dot(chromafb, stftFrames[-1])
    norm_chroma = librosa.util.normalize(raw_chroma, norm=norm, axis=0)
    chromaFrames.append(norm_chroma)

    i += 1

chromaFramesNp = np.array(chromaFrames)
plt.imshow(chromaFramesNp[:30])

#%%
# from utils import getReferenceChromas
refChromasUtils = getReferenceChromas(Path('jetee.wav'), sr = 44100, n_fft = 4096, window_length = 2048,
                        hop_length = 1024, chromaType = "stft", n_chroma = 12,
                        norm=np.inf)
plt.imshow(refChromasUtils[:30])
#%%
recordedChromasNew = np.load("recordedChromas_New.npy")
plt.imshow(recordedChromasNew[:30])
