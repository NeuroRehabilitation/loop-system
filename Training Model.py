from Signals_Processing import *
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn import ensemble, feature_selection
import pickle

"""Load Data from Folder"""

folder = "C://Users//Rodrigo//Desktop//PhD//Study2//Training Models//"
participant = "P1"
path = folder + participant

os.chdir(path)
(
    users,
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

for root, dirs, files in os.walk(path):
    for fname in files:
        if fname.endswith(".xdf"):
            users[fname] = Run_files(fname)

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
    valence,
    arousal,
) = getEvents(users, "PsychoPy Markers", "PsychoPy Ratings")
print(valence)
print(arousal)
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
dataframe_EEG = getEEGDataframe(features_epochs_EEG)
dataframe = getSignalsDataframe(features_epochs)

"""Concatenate Dataframes"""
columns = dataframe.columns[: (len(dataframe.columns) - 2)]
columns_EEG = dataframe_EEG.columns[: (len(dataframe_EEG.columns) - 2)]
full_dataframe = pd.concat([dataframe_EEG[columns_EEG], dataframe], axis=1)
full_columns = full_dataframe.columns[: (len(full_dataframe.columns) - 2)]

"""Scaler"""
scaler = StandardScaler()

"""Input Data for Models"""
X = np.array(full_dataframe[full_columns])
Y = np.array(full_dataframe[["Category"]])

"""Imputer for Nan"""
imp = SimpleImputer(missing_values=np.nan, strategy="mean")
imp.fit(X)
X = imp.transform(X)

"""Train Model"""

model = ensemble.RandomForestClassifier(random_state=0)
scaler = scaler.fit(X, Y.ravel())
X = scaler.transform(X)
rfe = feature_selection.RFE(model, step=1)
rfe = rfe.fit(X, Y.ravel())
X = rfe.transform(X)
model.fit(X, Y.ravel())

with open(path + "//" + "imp.pkl", "wb") as f:
    pickle.dump(imp, f)
with open(path + "//" + "scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)
with open(path + "//" + "rfe.pkl", "wb") as f:
    pickle.dump(rfe, f)
with open(path + "//" + "model.pkl", "wb") as f:
    pickle.dump(model, f)
