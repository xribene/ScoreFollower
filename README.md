# ScoreFollower

## How to use

- Make sure TouchDesigner is not open
- Open terminal
- Activate the conda environment
    - conda activate gids
- Navigate to *ScoreFollower* directory and run the main.py file
    - python main.py
- Now you can open TouchDesigner

## OSC Protocol

- ScoreFollower sends messages to port 54000 and receives/listens to port 54001
- TouchDesigner should listen to port 54001 and send to 54000
- QLab communicates *only* with TouchDesigner using ports 53000/53001

### ScoreFollower output signals
- /bar/{barNumber}
    - GuiClasses.py - function sendBarTrigger - line 346
- /workspace/{workspaceID}/playhead/{cueName}
    - GuiClasses.py - function sendCueTrigger - line 342
    - I kept the *workspace* and *playhead* tags only in case you want to demonstrate the connection with QLab
- /start
    - It is sent when the user starts the ScoreFollower either by manually hitting the button in the GUI or by sending a */reponse/start* message from TouchDesigner
- /stop
    - Similar as /start

### ScoreFollower input signals
All the osc signals received from TouchDesigner should start with */response*. This doens't make a lot of sense, but we ll change it later. I think it would be usefull to have a different tag for TouchDesigner's output messages depending on if they are custom or some automated ones that TD sends anyway (I don't know if that happens at all).

- /response/setBar/{barNumber}
    - You should automatically see the GUI update the bar number box (the cue number box won't be updated untill the alignment reaches the next cue)
- /response/setCue/{cueName}
    - Similar
- /response/start
    - Starts the ScoreFollower. In the case it's already started, then this signal is ignored.
- /response/stop
    - Similar
- /response/startStop
    - Set the playing status to the opposite of the current one.
- /response/reset
    - Resets and stops the ScoreFollower. You ll have to send a */response/start* message to start again
- /response/nextSection
    - Stops the ScoreFollower and loads the next section of the same piece
    - The succession of the sections is defined in the names of their directory. For example, inside the Jetee folder currently there is *1_ThemeA*. If you want to add the next section, the folders name should be in the form of *2_{sectioName}*
- /response/nextPiece
    - Stops the ScoreFollower and loads the next piece.
    - Haven't defined a succession scheme yet. In the future I ll change this so you can send the exact piece's name in the osc command.

## Requirements
- python > 3.6
- PyQt > 5.12
- music21
- librosa
- scipy
