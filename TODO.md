# GUI
<input type="checkbox" checked> Live RMS indicator  <br>
<input type="checkbox" checked> Edit box to enter starting measure/cue <br>
<input type="checkbox" checked> dropdown menu to select audio interface inputs/outputs <br>
<input type="checkbox" checked> playlist <br>
<input type="checkbox"> add option to choose recording channels <br>
<input type="checkbox"> osc receiver box - delete old messages to prevent overflow

---

# OSC Communication
<input type="checkbox" > send message when starting or stopping <br>
<input type="checkbox" > accept feedback messages from user <br>


---

# Alignment Algorithm
<input type="checkbox" checked> option to start from specific index/measure <br>
<input type="checkbox" checked> accept feedback from user to go back and forth in the reference score <br>
<input type="checkbox" checked> optimize for loops - 10x performance <br>

---

# Other
<input type="checkbox" checked> change everything to 22khz <br>
<input type="checkbox" checked> run experiments with real-time tempo change <br>

---

- added cue and bar ticks in axes
- fixed output dropdown


# TODO


- Update code for chroma visualizer (4 horizontal lines - combo of offline chromas vs online chromas)
- Compare rendered chromas vs recording chromas / choose filterbanks and variables from config file
- test Mullers CENS

- step by step visualize old algorithm
- look ahead algorithm implementation

# DONE
- ADD TUNING - almost done - average over 500frames
- add option to choose recording channels
- osc receiver box - delete old messages to prevent overflow - NEEDS TESTING
- Compare path using cosine distance - DOesnt work
- send message when starting or stopping - Needs Testing
- accept feedback messages from user 


- Find a the piece that doesn't work (number 6)
- Make sure that themaA still works
- Create new renderings using musescore. Does it work now ? 
- Check also what happens in offline DTW

# DONE 5/27/2022

- print xml and wav durations when calculating chromas

- send osc "channel" data ( > 10FPS)
    - progress bar percentage
    - rms audio values
    - current BPM
    
- real time tempo estimation
    - each frame corresponds to 512audio samples = 23ms
    - update it every second. I know how many frames per second (43.0664)
    - every x updates, I check how many seconds passed (dd), and how many frames passed (ff)
    - for 1s --> 43.0064 frames
    - for dd --> ddF
    - newBPM = ddF/ff * initialBPM
    - Done, but I store it in status, while it should be sent often "channel", along with progress bar.

realtime channel . send current bpm / current percentage progress / rms val




