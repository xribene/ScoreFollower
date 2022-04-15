# ScoreFollower

## How to use

- **Make sure TouchDesigner is not open**
    - This is a bug from ScoreFollower's side. It can be fixed but it requires a lot of digging
- Open terminal and activate the conda environment
    - conda activate gids
- Navigate to *ScoreFollower* directory 
- Make sure you have the latest code
    - git checkout master  (to ensure that you are on the master branch and not the development one)
    - git pull 
- Open ScoreFollower
    - python main.py
- **Now you can open TouchDesigner**

--- 

## OSC Protocol

- ScoreFollower sends messages to port 54000 and receives/listens to port 54001
- TouchDesigner should listen to port 54001 and send to 54000 (for communicating with ScoreFollower)
- QLab communicates *only* with TouchDesigner using ports 53000/53001

### ScoreFollower output signals

I add the corresponding lines in the code in case you want to change the form of the osc addresses.

- **/bar/{barNumber}**
    - GuiClasses.py - function sendBarTrigger - line 346
- **/workspace/{workspaceID}/playhead/{cueName}**
    - GuiClasses.py - function sendCueTrigger - line 342
    - I kept the *workspace* and *playhead* tags only in case you want to demonstrate the connection with QLab. We don't need them for TD.
- **/start**
    - It is sent when the user starts the ScoreFollower either by manually hitting the button in the GUI or by sending a */reponse/start* message from TouchDesigner
- **/stop**
    - Similar as /start

### ScoreFollower input signals
All the osc signals received from TouchDesigner should start with */response*. This doens't make a lot of sense, but we ll change it later. I think it would be usefull to have a different tag for TouchDesigner's output messages depending on if they are custom or some automated ones that TD sends anyway (I don't know if that happens at all).

- **/response/setBar/{barNumber}**
    - You should automatically see the GUI update the bar number box (the cue number box won't be updated untill the alignment reaches the next cue)
- **/response/setCue/{cueName}**
    - Similar
- **/response/start**
    - Starts the ScoreFollower. In the case it's already started, then this signal is ignored.
- **/response/stop**
    - Similar
- **/response/startStop**
    - Set the playing status to the opposite of the current one.
- **/response/reset**
    - Resets and stops the ScoreFollower. You ll have to send a */response/start* message to start again
- **/response/nextSection**
    - Stops the ScoreFollower and loads the next section of the same piece
    - The succession of the sections is defined in the names of their directory. For example, inside the Jetee folder currently there is *1_ThemeA*. If you want to add the next section, the folders name should be in the form of *2_{sectioName}*
    -  If we are already in the "last" section, then it doesn't have any effect
- **/response/nextPiece**
    - Stops the ScoreFollower and loads the next piece.
    - Haven't defined a succession scheme yet. 
    - If we are already in the "last" piece, then it doesn't have any effect
- **/response/prevSection**
    - Similar
- **/response/prevPiece**
    - Similiar
- **/response/setPiece/{pieceName}**
    - Sets the piece by name. Currently {pieceName} can be either Jetee or Stravinsky
    - It does nothing if the name is invalid

---

## Requirements
- python > 3.6
- PyQt > 5.12
- music21
- librosa
- scipy
