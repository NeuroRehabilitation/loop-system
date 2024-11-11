import time
import warnings

import joblib
from sklearn.ensemble import VotingClassifier

from Signals_Processing import *

warnings.filterwarnings("ignore")

start_time = time.time()

"""Load Data from Folder"""

folder = os.getcwd() + "\\Training Models\\"

# Prompt user to enter participant ID
participant = input("Enter the participant ID (e.g., P3): ").strip()

path = folder + participant

data = {}
fs = 100
resolution = 16
sensors = ["ECG", "EDA", "RESP"]

try:
    if os.path.isdir(path):
        print(f"Loading data from {path}.")

        xdf_files = [file for file in os.listdir(path) if file.endswith(".xdf")]

        if not xdf_files:
            print("No .xdf files found.")
        else:
            for file in xdf_files:
                file_path = os.path.join(path, file)

                condition = file.split("_")[1].split(".")[0]

                data[condition] = Run_files(file_path)
    else:
        raise FileNotFoundError(f"The directory {path} does not exist.")
        sys.exit(1)

except FileNotFoundError:
    print(f"The directory {path} does not exist.")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit()

"""Signals Processing"""
signals = getSignals(
    data, "OpenSignals", "PsychoPy Markers", "PsychoPy Ratings", sensors=sensors
)
epochs_markers, ratings = getEvents(signals)

"""Baseline Dataframe"""
baseline_signals = nk.epochs_create(
    pd.DataFrame.from_dict(signals["Baseline"]["Signals"]),
    events=epochs_markers["Baseline"]["Onset_index"],
    sampling_rate=fs,
    epochs_start=0,
    epochs_end=epochs_markers["Baseline"]["EventsDiff"],
)
df_baseline = getDataframe(baseline_signals["1"], fs, resolution)

try:
    df_baseline.to_csv(path + "\\df_baseline.csv", sep=";")
    print(f"Baseline Dataframe saved to {path}.")
except Exception as e:
    print(f"An error occurred saving the Baseline Dataframe: {e}")

"""Create epochs from signals"""
epochs_data = getSignalsEpochs(signals, epochs_markers, ratings, window=60, fs=fs)
print("Epochs Created Successfully.")

"""Extract features from Epochs"""
features = getFeatures(epochs_data, fs=fs, resolution=resolution)

"""Features Dataframe"""
dataframe = getSignalsDataframe(features, epochs_data)
dataframe.replace([np.inf, -np.inf], np.nan, inplace=True)

try:
    dataframe.to_csv(path + "\\dataframe.csv", sep=";")
    print(f"Features Dataframe saved to {path}.")
except Exception as e:
    print(f"An error occurred saving the Features Dataframe: {e}")

"""Subtract baseline features to dataframe"""
columns = dataframe.columns[: len(dataframe.columns) - 3]
full_dataframe = getFullDataframe(dataframe, df_baseline, columns)

try:
    full_dataframe.to_csv(path + "\\full_dataframe.csv", sep=";")
    print(f"Full Dataframe saved to {path}.")
except Exception as e:
    print(f"An error occurred saving the Full Dataframe: {e}")

# full_dataframe = pd.read_csv(path + "\\full_dataframe.csv", sep=";")
# columns = full_dataframe.columns[:(len(full_dataframe.columns) - 3)]

"""Input Data for Models"""
X = np.array(full_dataframe[columns])
Y = np.array(full_dataframe[["Arousal"]])

"""GridSearchCV"""
best_models = gridSearchCV(X, Y)


# Sort the models by their best score in descending order
sorted_models = sorted(
    best_models.items(), key=lambda item: item[1]["best_score"], reverse=True
)

# Select the top two models
best_two_models = sorted_models[:2]

estimators = [
    (model_name, info["best_estimator"]) for model_name, info in best_two_models
]

# Create a VotingClassifier with the best two models
voting_clf = VotingClassifier(
    estimators=estimators, voting="soft"
)  # You can also use 'hard' voting
voting_clf.fit(X, Y.ravel())

try:
    joblib.dump(voting_clf, f"{path}/model.pkl")
    print(f"VotingClassifier saved successfully to {path}")
except Exception as e:
    print(f"Error saving the model: {e}")

print(f'Elapsed time = {(time.time()-start_time)/60:.2f} minutes')