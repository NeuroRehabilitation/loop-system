from Process_Features import *


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


def getSignalsEpochs(data: dict, onset_index: dict, events_diff: dict, fs: int) -> dict:
    epochs = {}

    for users in data.keys():
        epochs[users] = nk.epochs_create(
            data[users]["Signals"],
            events=onset_index[users],
            sampling_rate=fs,
            epochs_start=0,
            epochs_end=events_diff[users],
        )

    return epochs


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
def getFeatures(data: dict, fs: int, resolution: int) -> dict:
    features_signals = {}

    for users in data.keys():
        temp_dict = {}
        for key in data[users].keys():
            temp_dict[key] = getDataframe(data[users][key], fs, resolution)
        features_signals[users] = temp_dict

    return features_signals


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


@staticmethod
def getSignalsDataframe(features_epochs: dict):
    category, videos = [], []

    for key in features_epochs.keys():
        user = key
    video = list(features_epochs[user].keys())
    df = pd.DataFrame(columns=features_epochs[user][video[0]].columns)
    for users in features_epochs.keys():
        for epoch in features_epochs[users].keys():
            if epoch != "baseline":
                df = pd.concat([df, features_epochs[users][epoch]], ignore_index=True)
                category.append(epoch.split("/")[1])
                videos.append(epoch.split("/")[2])
    df["Category"] = category
    df["Video"] = videos

    return df
