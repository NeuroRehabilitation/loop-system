import pyxdf
from colorama import Fore
from tqdm import tqdm

from Epochs import *
from Load import *
from Process_Features import *


@staticmethod
def getSignals(data,
               openSignals_stream_name: str,
               markers_stream_name: str,
               ratings_stream_name: str,
               sensors: list, ) -> dict:
    signals = {}

    for condition in data:
        signals[condition] = Load_Data(data[condition], openSignals_stream_name, markers_stream_name,
                                       ratings_stream_name, sensors)

    return signals


@staticmethod
def getEvents(signals) -> (dict, dict):
    epochs_markers, ratings = {}, {}

    for condition in signals:
        onset, offset, marker = getMarkers(signals[condition]["Markers"], signals[condition]["Markers Timestamps"])
        onset_index, offset_index = getMarkersIndex(onset, offset, signals[condition]["Signals"]["Time"])
        events_diff = CalculateEventsDiff(onset, offset)
        epochs_markers[condition] = {"Onset": onset, "Onset_index": onset_index,
                                     "Offset": offset, "Offset_index": offset_index,
                                     "EventsDiff": events_diff,
                                     "Marker": marker}

        arousal_index = getRatingsIndex(signals[condition]["Ratings"]["Arousal Timestamps"],
                                        signals[condition]["Signals"]["Time"])
        valence_index = getRatingsIndex(signals[condition]["Ratings"]["Valence Timestamps"],
                                        signals[condition]["Signals"]["Time"])
        ratings[condition] = {"Arousal": signals[condition]["Ratings"]["Arousal"],
                              "Arousal Timestamps": signals[condition]["Ratings"]["Arousal Timestamps"],
                              "Arousal_index": arousal_index,
                              "Valence": signals[condition]["Ratings"]["Valence"],
                              "Valence Timestamps": signals[condition]["Ratings"]["Valence Timestamps"],
                              "Valence_index": valence_index}

    return epochs_markers, ratings


@staticmethod
def Run_files(fname):
    data, header = pyxdf.load_xdf(fname)

    return data


@staticmethod
def change_key(dictionary, key_to_remove, new_key):
    dictionary[new_key] = dictionary.pop(key_to_remove)


@staticmethod
def Load_Data(
        data,
        openSignals_stream_name: str,
        markers_stream_name: str,
        ratings_stream_name: str,
        sensors: list,
) -> dict:
    marker, timestamps = Load_PsychopyMarkers(data, markers_stream_name)
    opensignals_data, fs = Load_Opensignals(data, openSignals_stream_name)
    ratings = Load_Ratings(data, ratings_stream_name)

    change_key(opensignals_data, "time_Opensignals", "Time"), change_key(opensignals_data, "CH1", sensors[0]),
    change_key(opensignals_data, "CH2", sensors[1]), change_key(opensignals_data, "CH3", sensors[2])

    Signals = pd.DataFrame(data=opensignals_data)

    data = {
        "Signals": Signals,
        "Markers": marker,
        "Markers Timestamps": timestamps,
        "Ratings": ratings
    }

    return data


@staticmethod
def getDataframe(dataframe, fs, resolution):
    HRV_Dataframe = Process_HRV(dataframe["ECG"], fs, resolution)
    RESP_Dataframe = Process_RESP(dataframe["RESP"], fs, resolution)
    EDA_Dataframe = Process_EDA(dataframe["EDA"], fs, resolution)
    Dataframe = (HRV_Dataframe.join(EDA_Dataframe)).join(RESP_Dataframe)

    return Dataframe


@staticmethod
def filterEEG(data: dict, EEG_fs: int) -> dict:
    EEG_filtered = {}

    for keys in data.keys():
        temp_dict = {}
        for i in range(1, 33):
            temp_dict["EEG_" + str(i)] = EEG.filterData(
                EEG.ICA(data[keys]["EEG"]["EEG_" + str(i)]), EEG_fs
            )
        EEG_filtered[keys] = temp_dict

    return EEG_filtered


@staticmethod
def getEEGChannels(EEG_filtered: dict) -> dict:
    for users in EEG_filtered.keys():
        EEG_filtered[users] = pd.DataFrame.from_dict(EEG_filtered[users])

    return EEG_filtered


@staticmethod
def getEpochs(data: dict, onset_index: dict, events_diff: dict, fs: int) -> dict:
    epochs = {}

    for users in data.keys():
        epochs[users] = nk.epochs_create(
            data[users],
            events=onset_index[users],
            sampling_rate=fs,
            epochs_start=0,
            epochs_end=events_diff[users],
        )

    return epochs


@staticmethod
def getSignalsEpochs(signals: dict, epochs_markers: dict, ratings: dict, window: int, fs: int) -> dict:
    epochs_data = {}

    for condition in epochs_markers:
        events = np.arange(epochs_markers[condition]["Onset_index"][0],
                           epochs_markers[condition]["Offset_index"][-1] - window * fs, fs)

        stroop_markers = [0]

        for timestamp_index in epochs_markers[condition]["Onset_index"]:
            stroop_markers.append(
                len(np.where(timestamp_index >= events)[0]))

        count = np.diff(stroop_markers)
        markers = [value for count, value in zip(
            count, epochs_markers[condition]["Marker"]) for _ in range(count)]

        arousal_values = markers
        valence_values = markers

        epochs_signals = nk.epochs_create(pd.DataFrame.from_dict(signals[condition]["Signals"]),
                                          events=events,
                                          sampling_rate=fs,
                                          epochs_start=0,
                                          epochs_end=window,
                                          )

        epochs_data[condition] = {"Signals": epochs_signals, "Arousal": arousal_values, "Valence": valence_values}

    return epochs_data


@staticmethod
def getFeatures(epochs_data: dict, fs: int, resolution: int) -> dict:
    # ANSI escape code for blue
    BLUE = "\033[94m"

    features = {}

    for condition in tqdm(epochs_data):
        features[condition] = {}
        for epoch in tqdm(epochs_data[condition]["Signals"],
                          desc=Fore.BLUE + f"Extracting feature for {condition}" + Fore.BLUE,
                          colour="cyan",
                          bar_format=BLUE + "{l_bar}" + BLUE + "{bar}" + BLUE + "| " + BLUE + "{n_fmt}" + BLUE + "/" + BLUE + "{total_fmt} [" + BLUE + "{elapsed}" + "<" + BLUE + "{remaining}" + ", " + "{rate_fmt}""]",
                          leave=False):
            features[condition][epoch] = getDataframe(epochs_data[condition]["Signals"][epoch], fs, resolution)

    tqdm().set_description("All Conditions Processed")

    return features


@staticmethod
def getFeaturesEpochs(data: dict) -> tuple:
    features_epochs, baseline_dict = {}, {}
    df_baseline = pd.DataFrame()
    for user in data.keys():
        temp_dict = {}
        for video in data[user].keys():
            df_test = pd.DataFrame()

            if video != "baseline":
                for feature in data[user][video].columns:
                    df_test[feature] = (
                            data[user][video][feature] - data[user]["baseline"][feature]
                    )
                temp_dict[video] = df_test
            elif video == "baseline":
                for feature in data[user][video].columns:
                    df_baseline[feature] = data[user]["baseline"][feature]

        features_epochs[user] = temp_dict
        baseline_dict[user] = df_baseline

    return features_epochs, baseline_dict


@staticmethod
def getSignalsDataframe(features: dict, epochs_data: dict):
    BLUE = "\033[94m"

    dataframe = pd.DataFrame(columns=features["Baseline"]["1"].columns)
    users, conditions, arousal, valence = [], [], [], []

    for condition in tqdm(features):
        arousal.extend(epochs_data[condition]["Arousal"])
        valence.extend(epochs_data[condition]["Valence"])

        for epoch in tqdm(features[condition],
                          desc=Fore.BLUE + f"Concatenating Features in Dataframe for {condition}" + Fore.BLUE,
                          colour="cyan",
                          bar_format=BLUE + "{l_bar}" + BLUE + "{bar}" + BLUE + "| " + BLUE + "{n_fmt}" + BLUE + "/" + BLUE + "{total_fmt} [" + BLUE + "{elapsed}" + "<" + BLUE + "{remaining}" + ", " + "{rate_fmt}""]",
                          leave=False):
            conditions.append(condition + "_" + epoch)
            dataframe = pd.concat([dataframe, features[condition][epoch]], ignore_index=True)

    # dataframe["Arousal"] = arousal
    # dataframe["Valence"] = valence
    dataframe["Condition"] = conditions
    dataframe = dataframe.rename(
        columns={"AVG": "AVG_RSP_Rate", "Maximum": "Max_RSP_Rate", "Minimum": "Min_RSP_Rate", "STD": "STD_RSP_Rate"})

    return dataframe


@staticmethod
def getVideosDict(epochs: dict, videos: dict) -> dict:
    dict = {}

    for users in epochs.keys():
        temp_dict = {}
        for i, keys in enumerate(epochs[users].keys()):
            temp_dict[videos[users][i]] = epochs[users][keys]
        dict[users] = temp_dict

    return dict


@staticmethod
def getEEGBands(EEG_dict: dict, EEG_fs: int) -> dict:
    features_EEG = {}

    for users in EEG_dict.keys():
        temp_dict = {}
        for key in EEG_dict[users].keys():
            new_dict = {}
            for i in range(1, 33):
                band_power = EEG.frequencyAnalysis(
                    EEG_dict[users][key]["EEG_" + str(i)], EEG_fs
                )
                new_dict["EEG_" + str(i)] = band_power
            temp_dict[key] = new_dict
        features_EEG[users] = temp_dict

    return features_EEG


@staticmethod
def getEEGDict(features_EEG: dict) -> tuple:
    features_epochs_EEG, features_baseline_EEG = {}, {}

    for user in features_EEG.keys():
        temp_dict, channel_dict = {}, {}
        for video in features_EEG[user].keys():
            if video != "baseline":
                channel_dict = dict()
                for channel in features_EEG[user][video].keys():
                    band_dict = {}
                    for feature in features_EEG[user][video][channel].keys():
                        band_dict[feature] = (
                                features_EEG[user][video][channel][feature]
                                - features_EEG[user]["baseline"][channel][feature]
                        )
                    channel_dict[channel] = band_dict
                temp_dict[video] = channel_dict
            elif video == "baseline":
                for channel in features_EEG[user][video].keys():
                    band_dict = {}
                    for feature in features_EEG[user][video][channel].keys():
                        band_dict[feature] = features_EEG[user]["baseline"][channel][
                            feature
                        ]
                    channel_dict[channel] = band_dict

        features_epochs_EEG[user] = temp_dict
        features_baseline_EEG[user] = channel_dict

    return features_epochs_EEG, features_baseline_EEG


@staticmethod
def getEEGDataframe(features_epochs_EEG: dict, features_baseline_EEG: dict):
    columns = list()
    category, video = [], []

    for key in features_epochs_EEG.keys():
        user = key
    videos = list(features_epochs_EEG[user].keys())
    for epochs in features_epochs_EEG[user][videos[0]].keys():
        for bands in features_epochs_EEG[user][videos[0]][epochs].keys():
            columns.append(epochs + "_" + bands)
    df_EEG = pd.DataFrame(columns=columns)
    baseline_df = pd.DataFrame(columns=columns)

    for users in features_epochs_EEG.keys():
        temp_df = pd.DataFrame(columns=columns)
        baseline_list = list()

        for channel in features_baseline_EEG[users].keys():
            for band in features_baseline_EEG[users][channel].keys():
                baseline_list.append(features_baseline_EEG[users][channel][band])

        baseline_df.loc[0] = baseline_list

        for i, videos in enumerate(features_epochs_EEG[users].keys()):
            if videos != "baseline":
                temp_list = list()
                for channel in features_epochs_EEG[users][videos].keys():
                    for band in features_epochs_EEG[users][videos][channel].keys():
                        temp_list.append(
                            features_epochs_EEG[users][videos][channel][band]
                        )
                temp_df.loc[i] = temp_list
                category.append(videos.split("/")[1])
                video.append(videos.split("/")[2])

        df_EEG = pd.concat([df_EEG, temp_df], ignore_index=True)
    df_EEG["Category"] = category
    df_EEG["Video"] = video

    return df_EEG, baseline_df
