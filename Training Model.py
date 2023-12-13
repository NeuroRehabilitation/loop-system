import warnings
from Signals_Processing import *
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn import ensemble, feature_selection
import pickle

warnings.filterwarnings("ignore")

"""Load Data from Folder"""

folder = os.getcwd() + "\\Training Models\\"
participant = "P0"
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

Opensignals_fs = 100
EEG_fs = 250
resolution = 16
sensors = ["ECG", "EDA", "RESP"]

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
) = getEvents(
    users,
    "OpenSignals",
    "openvibeSignal",
    "PsychoPy Markers",
    "PsychoPy Ratings",
    sensors,
)

"""EEG Processing"""

EEG_filtered = filterEEG(data, EEG_fs)
EEG_filtered = getEEGChannels(EEG_filtered)
EEG_epochs = getEpochs(EEG_filtered, onset_index_EEG, events_diff, EEG_fs)
EEG_dict = getVideosDict(EEG_epochs, videos)
features_EEG = getEEGBands(EEG_dict, EEG_fs)
features_epochs_EEG, features_baseline_EEG = getEEGDict(features_EEG)

"""Biosignalsplux Processing"""

Signals_epochs = getSignalsEpochs(data, onset_index, events_diff, Opensignals_fs)
Signals = getVideosDict(Signals_epochs, videos)
features_signals = getFeatures(Signals, Opensignals_fs, resolution)
features_epochs, df_baseline = getFeaturesEpochs(features_signals)
df_baseline[participant].to_csv(path + "\\baseline.csv", sep=";")

"""Dataframes"""
dataframe_EEG, EEG_baseline = getEEGDataframe(
    features_epochs_EEG, features_baseline_EEG
)
dataframe = getSignalsDataframe(features_epochs)
EEG_baseline.to_csv(path + "\\EEGbaseline.csv", sep=";")

"""Concatenate Dataframes"""
columns = dataframe.columns[: (len(dataframe.columns) - 2)]
columns_EEG = dataframe_EEG.columns[: (len(dataframe_EEG.columns) - 2)]
full_dataframe = pd.concat([dataframe_EEG[columns_EEG], dataframe], axis=1)
full_dataframe["Valence Level"] = valence[participant]
full_dataframe["Arousal Level"] = arousal[participant]
full_columns = full_dataframe.columns[: (len(full_dataframe.columns) - 4)]

"""Scaler"""
scaler, scaler_arousal, scaler_valence = (
    StandardScaler(),
    StandardScaler(),
    StandardScaler(),
)

"""Input Data for Models"""
X = np.array(full_dataframe[full_columns])
X_arousal = np.array(full_dataframe[full_columns])
X_valence = np.array(full_dataframe[full_columns])

Y = np.array(full_dataframe[["Category"]])
Y_arousal = np.array(full_dataframe[["Arousal Level"]])
Y_valence = np.array(full_dataframe[["Valence Level"]])

"""Train Model"""
imp = SimpleImputer(missing_values=np.nan, strategy="mean")
imp.fit(X)
X = imp.transform(X)
model = ensemble.RandomForestClassifier()
scaler = scaler.fit(X, Y.ravel())
X = scaler.transform(X)
rfe = feature_selection.RFE(model, step=1)
rfe = rfe.fit(X, Y.ravel())
X = rfe.transform(X)
model.fit(X, Y.ravel())

try:
    with open(path + "//" + "imp.pkl", "wb") as f:
        pickle.dump(imp, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "rfe.pkl", "wb") as f:
        pickle.dump(rfe, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "model.pkl", "wb") as f:
        pickle.dump(model, f)
except Exception as e:
    print(e)

"""Arousal Model"""

imp_arousal = SimpleImputer(missing_values=np.nan, strategy="mean")
imp_arousal.fit(X_arousal)
X_arousal = imp.transform(X_arousal)
model_arousal = ensemble.RandomForestClassifier(random_state=0)
scaler_arousal = scaler_arousal.fit(X_arousal, Y_arousal.ravel())
X_arousal = scaler_arousal.transform(X_arousal)
rfe_arousal = feature_selection.RFE(model_arousal, step=1)
rfe_arousal = rfe_arousal.fit(X_arousal, Y_arousal.ravel())
X_arousal = rfe_arousal.transform(X_arousal)
model_arousal.fit(X_arousal, Y_arousal.ravel())

try:
    with open(path + "//" + "imp_arousal.pkl", "wb") as f:
        pickle.dump(imp_arousal, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "scaler_arousal.pkl", "wb") as f:
        pickle.dump(scaler_arousal, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "rfe_arousal.pkl", "wb") as f:
        pickle.dump(rfe_arousal, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "model_arousal.pkl", "wb") as f:
        pickle.dump(model_arousal, f)
except Exception as e:
    print(e)

"""valence Model"""

imp_valence = SimpleImputer(missing_values=np.nan, strategy="mean")
imp_valence.fit(X_valence)
X_valence = imp.transform(X_valence)
model_valence = ensemble.RandomForestClassifier(random_state=0)
scaler_valence = scaler_valence.fit(X_valence, Y_valence.ravel())
X_valence = scaler_valence.transform(X_valence)
rfe_valence = feature_selection.RFE(model_valence, step=1)
rfe_valence = rfe_valence.fit(X_valence, Y_valence.ravel())
X_valence = rfe_valence.transform(X_valence)
model_valence.fit(X_valence, Y_valence.ravel())

try:
    with open(path + "//" + "imp_valence.pkl", "wb") as f:
        pickle.dump(imp_valence, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "scaler_valence.pkl", "wb") as f:
        pickle.dump(scaler_valence, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "rfe_valence.pkl", "wb") as f:
        pickle.dump(rfe_valence, f)
except Exception as e:
    print(e)
try:
    with open(path + "//" + "model_valence.pkl", "wb") as f:
        pickle.dump(model_valence, f)
except Exception as e:
    print(e)
