import warnings
from Signals_Processing import *

warnings.filterwarnings("ignore")

"""Load Data from Folder"""

folder = os.getcwd() + "\\Breathing Rate\\"
participant = "P0"
path = folder + participant

os.chdir(path)
(
    users,
    Signals_epochs,
    Signals,
    features_signals,
    features_epochs,
) = ({}, {}, {}, {}, {})

for root, dirs, files in os.walk(path):
    for fname in files:
        if fname.endswith(".xdf"):
            users[fname] = Run_files(fname)

Opensignals_fs = 100
resolution = 16
sensors = ["ECG", "EDA", "RESP"]

(
    events_diff,
    videos,
    onset,
    offset,
    onset_index,
    offset_index,
    data,
) = getEvents(users, "OpenSignals", "PsychoPy Markers", sensors)

"""Biosignalsplux Processing"""

Signals_epochs = getSignalsEpochs(data, onset_index, events_diff, Opensignals_fs)
Signals = getVideosDict(Signals_epochs, videos)
features_signals = getFeatures(Signals, Opensignals_fs, resolution)
features_epochs, df_baseline = getFeaturesEpochs(features_signals)

print("Baseline Respiration Rate = {}".format(df_baseline[participant]["AVG"][0]))
