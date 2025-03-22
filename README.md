# Multi Object Gravity Simulator
A simple gravity simulator in python

## How to run
* Suggest IDE(like pyCharm) to run the simulation.


1. Download the latest 'tag' file and unzip it in your interpreter. If you use pyCharm, then put the file in PycharmProjects folder
2. (If using Pycharm) Go to interpreter settings and configure python interpreter ** to python version 3.8 or higher
3. Install pygame to the interpreter (version higher than pygame 2.6.0 is fine) using pip or using pycharm interpreter settings
4. Open the project folder (multi object gravity simulator)
5. Run main.py 

** If 'Invalid Python interpreter selected ...' message comes out, click on 'Configure Python interpreter' and add one! Any interpreter of Python version greater or equal to 3.8 is ok.


## Features
- (key up, down, right, left): camara movement 
- (mouse click on a matter): lock center on a matter, click again to unlock (resizing window also unlocks)
- (mouse wheel): zoom in and zoom out
- (mouse click&drag): camara movement 
- press 'v' to toggle VERBOSE and UI
- press 't' to toggle Trail
- press 'ESC'/'Space' to pause in simulation screen (pause)


## Sample run




## history

2025.03.18 Basic program with rough calculation

2025.03.19 Detailed calculation and handled collision.
Added text, musics UI


2025.03.20 Separated camera coordinate  
Added zoom feature (this took so long to debug)    
Added trajectory (removed current trace system)     
Added Drawable - Matter hierarchy (will use Drawables for astroid particle, dust or background etc.)    
Artificial crafts can be added (they also belong to matter but saved separately)    


2025.03.21 Mouse click&drag also moves camera   
Added leapfrog, RK4 calculation   
Added buttons    
Added pause screen and main menu    


2025.03.22 Resizable window    
Added help screen 
Added system selection & toggle simulation method in main menu


2025.03.23 Preview system selection (using jacket images)   
Added controllable artificial matters! 


2025.03.24 System maker & saver (UI for easy spawning of matter)


TBU
- collision effect particles
- change simulation speed (FPS or SPEED) in pause


## Some useful sites
Audio cutter
https://vocalremover.org/cutter



