# ScoreFollower

## Preprocessing / Offline

- TLDR;
    - Wrote a the function that exctracts the reference chroma vectors from either a xml score or a wav file. 

- The function **getReferenceChromas** exists in the script utils.py:
    ```python
    def getReferenceChromas(filePath, sr = 44100, n_fft = 4096, 
                            hop_length = 2048, chromaType = "cqt"):
    ```
- We can choose the resolution of the chroma vectors (n_fft, hop_length) as well as the spectrogram type ("cqt" or "stft")
- Experiment
    - Offline global DTW alignment between score chroma vectors and wav chroma vectors
        - score vs stft --> 78
        - score vs cqt  --> 63
        - ![score_vs_stft](src/main/python/offline/scoreVsStft_75.png)
        - ![score_vs_cqt](src/main/python/offline/scoreVsCqt_60.png)
    - Chroma vectors extracted from cqt spectrum match better to the chromas from the xml score.


## Online

- TLDR; 
    - Implemented the basic 3 modules
        - Audio Recorder (100%)
        - Chroma Extractor (100%)
        - Online DTW (50%)
    - Wrote a basic real time app that uses these modules. 

- The **Audio Recorder** module exists in the script AudioRecorder.py:
    - Accepts input from a specified audio stream. This can be either the microphone, or a wav file (for testing only)
    - Maintains an internal buffer to implement overlap between audio windows. 
    - Sends each frame to the **Chroma Extractor** module.

- The **Chroma Extractor** module exists in the script Chromatizer.py:
    - Accepts an audio frame from the **Audio Recorder** and converts calculates the chroma vector for this frame. 
    - It sends the chroma vector to the **Online DTW** module
    - > TODO : "cqt" mode doesn't work for the real time app. 

- The **Online DTW** module exists in the script OnlineDTW.py:
    - Implemented most of the algorithm. 
    - > TODO : There are still some minor bugs
    - > TODO : Add support for manual overwrite of the alignment position
- > TODO : Add a basic **OSC** module
- > TODO : Run a first test by next week. Make some dummy cues (i.e to indicate the beggining of each measure). Randomly Start/Pause the audio file to see how the alignment works.


## App Distribution/Packaging 

- TLDR; 
    - We have excecutable files for each OS (Windows, Mac, Linux)
- Refactored the project's code in order to use a tool called **fbs** 
- **fbs** help us create cross plattform excecutable files for **PyQt5** based python apps
- Disadvantage : Exe files can become very large (i.e >1GB), depending on what python libraries we need

## Requirements
- python=3.6
- PyQt = 5.12
- music21
- librosa
- scipy
- fbs