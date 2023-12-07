# Hololens 2 labeling base 
![Overview](doc/img/frame176.png)
--- 
## Overview
These tools are used to receive and save data from the Hololens 2,
the working application can be found under 

https://github.com/intuitive-robots/human-demonstration-ar/tree/labeling

## Structure
```
    _
    |- calibration         # after a camera calibration the result will be stored here 
    |- calibration-frames  # Only the images put here will be used by calibration.py
    |- doc                 # documentation 
    |- imgs                # single frames from video2label.py will be safed here 
    |- saves               # Uploaded data from the hololens will be put here
    |- videos              # videos to test can be stored here
```
## Scripts
### calibration.py
- Extracts camera calibration data from the images saved in calibration-frames
- Images have to contain an calibration checkerboard (https://markhedleyjones.com/projects/calibration-checkerboard-collection)
- Outputs the data to ```calibration\calibration.yaml```
### drifter.py
- Opens a websocket server to receive hololens connections
- Saves incoming data to a file in ```saves/``` (the last saved file will be stored in ```saves/meta.yaml```)
### fileio.py
- Utility for file loading and saving
### video2label.py
- Visualizer for the saved data 




