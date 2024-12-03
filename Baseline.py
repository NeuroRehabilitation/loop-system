import time
import warnings
from Signals_Processing import *

warnings.filterwarnings("ignore")

start_time = time.time()

"""Load Data from Folder"""

folder = os.path.join(os.getcwd(), "Models")

# Prompt user to enter participant ID
participant = input("Enter the participant ID (e.g., P0): ").strip()

path = os.path.join(folder, participant)
path = os.path.join(path, "Baseline")
data = {}
fs = 100
resolution = 16
sensors = ["ECG", "EDA", "RESP"]

start_time = time.time()

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
    pd.DataFrame.from_dict(signals["baseline"]["Signals"]),
    events=epochs_markers["baseline"]["Onset_index"],
    sampling_rate=fs,
    epochs_start=0,
    epochs_end=epochs_markers["baseline"]["EventsDiff"],
)
df_baseline = getDataframe(baseline_signals["1"], fs, resolution)

try:
    df_baseline.to_csv(path + "\\df_baseline.csv", sep=";")
    print(f"Time elapsed = {(time.time()-start_time):.2f} seconds.")
    print(f"Baseline Dataframe saved to {path}.")
except Exception as e:
    print(f"An error occurred saving the Baseline Dataframe: {e}")
