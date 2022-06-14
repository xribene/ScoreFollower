#%%
from offline.utils_offline import *
import argparse
from pathlib import Path
import numpy as np

"""
To generate chromas and cueList for the score AAA
Use this function in the command line like this 
    python extractCuesAndChromas.py --path resources/Pieces/{PieceName}/{PartName}

and should contain :
    1) ONE wav file named {PieceName}_{PartName}.wav - encoded as int16
    2) ONE xml file named {PieceName}_{PartName}.xml - it should include a cues part called "CUES"
    3) ONE mid file name {PieceName}_{PartName}.mid

If any of the conditions aren't true, then it raises and error. 

The parameters of the chroma extraction are in resources/config.json

# TODO in the future score will have its own config file.
# TODO The main.py GUI, should load the correct config file according to the score selected

"""
#%%
parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str,
                    help='A path that contains the xml score and the wav audio file')
parser.add_argument('--fmin', type=int,  default=0,
                    help='Cut freq of low pass filter')

parser.add_argument('--wav', type = str)
parser.add_argument('--mid', type = str)
parser.add_argument('--xml', type = str)
#%%
args = parser.parse_args()
if args.path:
    path = Path(args.path)
    pieceName = path.parts[-2]
    sectionName = "".join(path.parts[-1].split("_")[1:])
    wavFile = returnCorrectFile(path, "wav")
    midFile = returnCorrectFile(path, "mid")
    xmlFile = returnCorrectFile(path, "xml")

elif args.wav and args.xml:
    wavFile = Path(args.wav)
    # midFile = Path(args.mid)
    xmlFile = Path(args.xml)
    pieceName = 'unk'
    sectionName = 'unk'
    path = Path.cwd()

else:
    print(f'You need to provide either a path, or the file names explicitly')
#%%
config = Params("resources/config.json")

if args.fmin == 0:
    args.fmin = None

# args.xml = 'resources/Pieces/ChristosTests/06_DateThemeA/JetTEST_DateThemeA_musescoreExport.musicxml'
# args.xml = 'resources/Pieces/ChristosTests/06_DateThemeA/JetTEST_DateThemeA_musescoreExport.xml'
# args.wav = 'resources/Pieces/ChristosTests/06_DateThemeA/MusescoreRender22k.wav'
cuesDict, xmlSecondsDuration = getCuesDict(filePath = xmlFile, 
                                    sr = config.sr, # this is 22k
                                    hop_length = config.hop_length)
#%%
referenceChromas, wavSecondsDuration = getChromas(wavFile, 
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
                                magPower = config.magPower,
                                fmin = args.fmin,
                                useZeroChromas = bool(config.useZeroChromas)
                                )

print(f'XML duration : {xmlSecondsDuration} seconds')
print(f'WAV duration : {wavSecondsDuration} seconds')

chromasFile = path/f"referenceAudioChromas_{pieceName}_{sectionName}.npy"
if chromasFile.is_file():
    chromasFile.rename(path/f"referenceAudioChromas_{pieceName}_{sectionName}_OLD.npy")
    print("kept backup of old chromas")

cuesFile = path/f"cuesDict_{pieceName}_{sectionName}.npy"
if cuesFile.is_file():
    cuesFile.rename(path/f"cuesDict_{pieceName}_{sectionName}_OLD.npy")
    print("kept backup of old cues")

np.save(cuesFile, cuesDict)
print(f"saved new cues in {cuesFile}")
np.save(chromasFile, referenceChromas)
print(f"saved new chromas in {chromasFile}")
