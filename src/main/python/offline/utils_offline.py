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

def get_window(window, Nx, fftbins=True):
    """Compute a window function.

    This is a wrapper for `scipy.signal.get_window` that additionally
    supports callable or pre-computed windows.

    Parameters
    ----------
    window : string, tuple, number, callable, or list-like
        The window specification:

        - If string, it's the name of the window function (e.g., `'hann'`)
        - If tuple, it's the name of the window function and any parameters
          (e.g., `('kaiser', 4.0)`)
        - If numeric, it is treated as the beta parameter of the `'kaiser'`
          window, as in `scipy.signal.get_window`.
        - If callable, it's a function that accepts one integer argument
          (the window length)
        - If list-like, it's a pre-computed window of the correct length `Nx`

    Nx : int > 0
        The length of the window

    fftbins : bool, optional
        If True (default), create a periodic window for use with FFT
        If False, create a symmetric window for filter design applications.

    Returns
    -------
    get_window : np.ndarray
        A window of length `Nx` and type `window`

    See Also
    --------
    scipy.signal.get_window

    Notes
    -----
    This function caches at level 10.

    Raises
    ------
    ParameterError
        If `window` is supplied as a vector of length != `n_fft`,
        or is otherwise mis-specified.
    """
    if callable(window):
        return window(Nx)

    elif isinstance(window, (str, tuple)) or np.isscalar(window):
        # TODO: if we add custom window functions in librosa, call them here

        return ss.get_window(window, Nx, fftbins=fftbins)

    elif isinstance(window, (np.ndarray, list)):
        if len(window) == Nx:
            return np.asarray(window)

        raise 
    else:
        raise 

def hz_to_octs(frequencies, tuning=0.0, bins_per_octave=12):
    """Convert frequencies (Hz) to (fractional) octave numbers.

    Examples
    --------
    >>> librosa.hz_to_octs(440.0)
    4.
    >>> librosa.hz_to_octs([32, 64, 128, 256])
    array([ 0.219,  1.219,  2.219,  3.219])

    Parameters
    ----------
    frequencies   : number >0 or np.ndarray [shape=(n,)] or float
        scalar or vector of frequencies

    tuning        : float
        Tuning deviation from A440 in (fractional) bins per octave.

    bins_per_octave : int > 0
        Number of bins per octave.

    Returns
    -------
    octaves       : number or np.ndarray [shape=(n,)]
        octave number for each frequency

    See Also
    --------
    octs_to_hz
    """

    A440 = 440.0 * 2.0 ** (tuning / bins_per_octave)

    return np.log2(np.asanyarray(frequencies) / (float(A440) / 16))
def librosaFiltersChroma(
    sr,
    n_fft,
    n_chroma=12,
    tuning=0.0,
    ctroct=5.0,
    octwidth=2,
    norm=2,
    base_c=True,
    dtype=np.float32,
):
    """Create a chroma filter bank.

    This creates a linear transformation matrix to project
    FFT bins onto chroma bins (i.e. pitch classes).


    Parameters
    ----------
    sr        : number > 0 [scalar]
        audio sampling rate

    n_fft     : int > 0 [scalar]
        number of FFT bins

    n_chroma  : int > 0 [scalar]
        number of chroma bins

    tuning : float
        Tuning deviation from A440 in fractions of a chroma bin.

    ctroct    : float > 0 [scalar]

    octwidth  : float > 0 or None [scalar]
        ``ctroct`` and ``octwidth`` specify a dominance window:
        a Gaussian weighting centered on ``ctroct`` (in octs, A0 = 27.5Hz)
        and with a gaussian half-width of ``octwidth``.

        Set ``octwidth`` to `None` to use a flat weighting.

    norm : float > 0 or np.inf
        Normalization factor for each filter

    base_c : bool
        If True, the filter bank will start at 'C'.
        If False, the filter bank will start at 'A'.

    dtype : np.dtype
        The data type of the output basis.
        By default, uses 32-bit (single-precision) floating point.

    Returns
    -------
    wts : ndarray [shape=(n_chroma, 1 + n_fft / 2)]
        Chroma filter matrix

    See Also
    --------
    librosa.util.normalize
    librosa.feature.chroma_stft

    Notes
    -----
    This function caches at level 10.

    Examples
    --------
    Build a simple chroma filter bank

    >>> chromafb = librosa.filters.chroma(22050, 4096)
    array([[  1.689e-05,   3.024e-04, ...,   4.639e-17,   5.327e-17],
           [  1.716e-05,   2.652e-04, ...,   2.674e-25,   3.176e-25],
    ...,
           [  1.578e-05,   3.619e-04, ...,   8.577e-06,   9.205e-06],
           [  1.643e-05,   3.355e-04, ...,   1.474e-10,   1.636e-10]])

    Use quarter-tones instead of semitones

    >>> librosa.filters.chroma(22050, 4096, n_chroma=24)
    array([[  1.194e-05,   2.138e-04, ...,   6.297e-64,   1.115e-63],
           [  1.206e-05,   2.009e-04, ...,   1.546e-79,   2.929e-79],
    ...,
           [  1.162e-05,   2.372e-04, ...,   6.417e-38,   9.923e-38],
           [  1.180e-05,   2.260e-04, ...,   4.697e-50,   7.772e-50]])


    Equally weight all octaves

    >>> librosa.filters.chroma(22050, 4096, octwidth=None)
    array([[  3.036e-01,   2.604e-01, ...,   2.445e-16,   2.809e-16],
           [  3.084e-01,   2.283e-01, ...,   1.409e-24,   1.675e-24],
    ...,
           [  2.836e-01,   3.116e-01, ...,   4.520e-05,   4.854e-05],
           [  2.953e-01,   2.888e-01, ...,   7.768e-10,   8.629e-10]])

    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> img = librosa.display.specshow(chromafb, x_axis='linear', ax=ax)
    >>> ax.set(ylabel='Chroma filter', title='Chroma filter bank')
    >>> fig.colorbar(img, ax=ax)
    """

    wts = np.zeros((n_chroma, n_fft))

    # Get the FFT bins, not counting the DC component
    frequencies = np.linspace(0, sr, n_fft, endpoint=False)[1:]

    frqbins = n_chroma * hz_to_octs(
        frequencies, tuning=tuning, bins_per_octave=n_chroma
    )

    # make up a value for the 0 Hz bin = 1.5 octaves below bin 1
    # (so chroma is 50% rotated from bin 1, and bin width is broad)
    frqbins = np.concatenate(([frqbins[0] - 1.5 * n_chroma], frqbins))

    binwidthbins = np.concatenate((np.maximum(frqbins[1:] - frqbins[:-1], 1.0), [1]))

    D = np.subtract.outer(frqbins, np.arange(0, n_chroma, dtype="d")).T

    n_chroma2 = np.round(float(n_chroma) / 2)

    # Project into range -n_chroma/2 .. n_chroma/2
    # add on fixed offset of 10*n_chroma to ensure all values passed to
    # rem are positive
    D = np.remainder(D + n_chroma2 + 10 * n_chroma, n_chroma) - n_chroma2

    # Gaussian bumps - 2*D to make them narrower
    wts = np.exp(-0.5 * (2 * D / np.tile(binwidthbins, (n_chroma, 1))) ** 2)

    # normalize each column
    wts = librosaNormalize(wts, norm=norm, axis=0)

    # Maybe apply scaling for fft bins
    if octwidth is not None:
        wts *= np.tile(
            np.exp(-0.5 * (((frqbins / n_chroma - ctroct) / octwidth) ** 2)),
            (n_chroma, 1),
        )

    if base_c:
        wts = np.roll(wts, -3 * (n_chroma // 12), axis=0)

    # remove aliasing columns, copy to ensure row-contiguity
    return np.ascontiguousarray(wts[:, : int(1 + n_fft / 2)], dtype=dtype)

def tiny(x):
    # Make sure we have an array view
    x = np.asarray(x)

    # Only floating types generate a tiny
    if np.issubdtype(x.dtype, np.floating) or np.issubdtype(
        x.dtype, np.complexfloating
    ):
        dtype = x.dtype
    else:
        dtype = np.float32

    return np.finfo(dtype).tiny

def librosaNormalize(S, norm=np.inf, axis=0, threshold=None, fill=None):
    # Avoid div-by-zero
    if threshold is None:
        threshold = tiny(S)

    elif threshold <= 0:
        raise 

    if fill not in [None, False, True]:
        raise 

    if not np.all(np.isfinite(S)):
        raise 

    # All norms only depend on magnitude, let's do that first
    mag = np.abs(S).astype(float)

    # For max/min norms, filling with 1 works
    fill_norm = 1

    if norm == np.inf:
        length = np.max(mag, axis=axis, keepdims=True)

    elif norm == -np.inf:
        length = np.min(mag, axis=axis, keepdims=True)

    elif norm == 0:
        if fill is True:
            raise 

        length = np.sum(mag > 0, axis=axis, keepdims=True, dtype=mag.dtype)

    elif np.issubdtype(type(norm), np.number) and norm > 0:
        length = np.sum(mag ** norm, axis=axis, keepdims=True) ** (1.0 / norm)

        if axis is None:
            fill_norm = mag.size ** (-1.0 / norm)
        else:
            fill_norm = mag.shape[axis] ** (-1.0 / norm)

    elif norm is None:
        return S

    else:
        raise

    # indices where norm is below the threshold
    small_idx = length < threshold

    Snorm = np.empty_like(S)
    if fill is None:
        # Leave small indices un-normalized
        length[small_idx] = 1.0
        Snorm[:] = S / length

    elif fill:
        # If we have a non-zero fill value, we locate those entries by
        # doing a nan-divide.
        # If S was finite, then length is finite (except for small positions)
        length[small_idx] = np.nan
        Snorm[:] = S / length
        Snorm[np.isnan(Snorm)] = fill_norm
    else:
        # Set small values to zero by doing an inf-divide.
        # This is safe (by IEEE-754) as long as S is finite.
        length[small_idx] = np.inf
        Snorm[:] = S / length

    return Snorm