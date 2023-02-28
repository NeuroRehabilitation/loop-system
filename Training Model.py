from Signals_Processing import *


"""Load Data from Folder"""

folder = "C://Users//Rodrigo//Desktop//PhD//Study2//Training Models//"
participant = "P1"
path = folder + participant

os.chdir(path)
(
    user,
    EEG_epochs,
    EEG_filtered,
    Signals_epochs,
    Signals,
    EEG_dict,
    features_signals,
    features_EEG,
    features_epochs,
    features_epochs_EEG,
) = ({}, {}, {}, {}, {}, {}, {}, {}, {}, {})

for root, dirs, files in os.walk(path, ".xdf"):
    for fname in files:
        user[fname] = Run_files(fname)

Opensignals_fs = 1000
EEG_fs = 250
resolution = 16

(
    events_diff,
    videos,
    onset,
    offset,
    onset_index,
    offset_index,
    onset_index_EEG,
    offset_index_EEG,
    data,
) = getEvents(user)

"""EEG Processing"""

EEG_filtered = filterEEG(data, EEG_fs)
EEG_filtered = getEEGChannels(EEG_filtered)
EEG_epochs = getEpochs(EEG_filtered, onset_index_EEG, events_diff, EEG_fs)
EEG_dict = getVideosDict(EEG_epochs, videos)
features_EEG = getEEGBands(EEG_dict, EEG_fs)
features_epochs_EEG = getEEGDict(features_EEG)

"""Biosignalsplux Processing"""
Signals_epochs = getEpochs(data, onset_index, events_diff, Opensignals_fs)
Signals = getVideosDict(Signals_epochs, videos)
features_signals = getFeatures(Signals, Opensignals_fs, resolution)
features_epochs = getFeaturesEpochs(features_signals)

"""Dataframes"""
df_EEG = getEEGDataframe(features_epochs_EEG)
df = getSignalsDataframe(features_epochs)
