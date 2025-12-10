

'''
These parameters change the folder names and file names
'''
EXPERIMENT_TYPE = "thermalTest"
SENSOR_COUNT = 8
ROOT_LOG_DIR = "DataLog_Test"


'''
These parameters adjust the view
'''
HISTORY_SECONDS = 60
FAKE_INTERVAL_MS = 1000
VIEW_MODE_DEFAULT = "merged"


# Default GUI temperature units: "C" or "F"
TEMP_UNIT = "C"


'''
These parameters change the names that show up in the GUI
'''
SENSOR_NAMES = [
    "TC1",
    "TC2",
    "TC3",
    "TC4",
    "TC5",
    "TC6",
    "TC7",
    "TC8",
]

# Display labels for the two channels each sensor has
HOT_LABEL = "Hot"
COLD_LABEL = "Cold"


'''
None = Auto-scale. These apply to all plots.

Can adjust these prior to running the code or during the live plotting
'''
AXIS_X_MIN = None
AXIS_X_MAX = None
AXIS_Y_MIN = None
AXIS_Y_MAX = None


'''
This adjusts the position of the sensors in the split view mode
'''
PLOT_LAYOUT = {
    "split2": {
        "left":  [0, 1, 2, 3],
        "right": [4, 5, 6, 7],
    }
}


'''
Adjust Colors of graph

RGB format

'''

CURVE_COLORS = {
    "hot0":  (255, 0, 0),       "cold0": (150, 0, 0),
    "hot1":  (0, 200, 0),       "cold1": (0, 100, 0),
    "hot2":  (0, 0, 255),       "cold2": (0, 0, 150),
    "hot3":  (255, 165, 0),     "cold3": (180, 110, 0),
    "hot4":  (128, 0, 128),     "cold4": (90, 0, 90),
    "hot5":  (0, 128, 128),     "cold5": (0, 90, 90),
    "hot6":  (128, 128, 0),     "cold6": (90, 90, 0),
    "hot7":  (255, 20, 147),    "cold7": (180, 10, 100),
}