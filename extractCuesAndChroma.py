#%%
from offline.utils_offline import *
import argparse
from pathlib import Path
import numpy as np

"""
To generate chromas and cueList for the score AAA
Use this function in the command line like this 
    python extractCuesAndChromas.py --path /resources/Pieces/AAA

A directory called AAA should be exist in /resources/Pieces
and should contain :
    1) ONE wav file named AAA.wav - encoded as int16
    2) ONE xml file named AAA.xml - it should include a cues part called "CUES"
    3) ONE mid file name AAA.mid

If any of the conditions aren't true, then it raises and error. 

The parameters of the chroma extraction are in /resources/config.json

# TODO in the future score will have its own config file.
# TODO The main.py GUI, should load the correct config file according to the score selected

"""
#%%
parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, nargs='+',
                    help='A path that contains the xml score and the wav audio file')

args = parser.parse_args()
path = Path(args.path[0])
#%%
# path = Path("resources/Pieces/Piece/")
pieceName = path.parts[-1]
wavFile = returnCorrectFile(path, "wav")
midFile = returnCorrectFile(path, "mid")
xmlFile = returnCorrectFile(path, "xml")

config = Params("resources/config.json")

cuesDict = getCuesDict(filePath = xmlFile, 
                                    sr = config.sr, 
                                    hop_length = config.hop_length)
referenceChromas = getChromas(wavFile, 
                                sr = config.sr,
                                n_fft = config.n_fft, 
                                hop_length = config.hop_length,
                                window_length = config.window_length,
                                chromaType = config.chromaType,
                                n_chroma = config.n_chroma,
                                norm = config.norm,
                                normAudio = True,
                                windowType = config.window_type,
                                chromafb = None,
                                magPower = config.magPower
                                )

chromasFile = path/f"referenceAudioChromas_{pieceName}.npy"
if chromasFile.is_file():
    chromasFile.rename(path/f"referenceAudioChromas_{pieceName}_OLD.npy")
    print("kept backup of old chromas")

cuesFile = path/f"cuesDict_{pieceName}.npy"
if cuesFile.is_file():
    cuesFile.rename(path/f"cuesDict_{pieceName}_OLD.npy")
    print("kept backup of old cues")

np.save(cuesFile, cuesDict)
print(f"saved new cues in {cuesFile}")
np.save(chromasFile, referenceChromas)
print(f"saved new chromas in {chromasFile}")
