from Process_Features import *
from Signals_Processing import *
import pickle


class Processing:
    def __init__(self):
        self.info = []
        self.data = {}

    def getOpenSignals(self):
        for stream in self.info:
            if stream["Name"] == "OpenSignals":
                name = stream["Name"]
                fs = stream["Sampling Rate"]
                for key in self.data[name].keys():
                    if key.startswith("ECG"):
                        HRV_Dataframe = Process_HRV(self.data[name][key], fs, 16)
                        self.features = pd.concat(
                            [self.features, HRV_Dataframe], axis=1
                        )

                    elif key.startswith("EDA"):
                        EDA_Dataframe = Process_EDA(self.data[name][key], fs, 16)
                        self.features = pd.concat(
                            [self.features, EDA_Dataframe], axis=1
                        )

                    elif key.startswith("RESP"):
                        RESP_Dataframe = Process_RESP(self.data[name][key], fs, 16)
                        self.features = pd.concat(
                            [self.features, RESP_Dataframe], axis=1
                        )

        return self.features

    def getOpenvibe(self):
        for stream in self.info:
            if stream["Name"] == "openvibeSignal":
                fs = stream["Sampling Rate"]
                # EEG_filtered = filterEEG(self.data["openvibeSignal"], fs)
                # print(EEG_filtered)
                EEG_dict = {}
                for i, key in enumerate(self.data["openvibeSignal"]):
                    if i > 0 and i < 33:
                        channel = "EEG_" + str(i)
                        #         sensor = EEG(self.data["openvibeSignal"][key], fs, 16)
                        EEG_dict[channel] = EEG.frequencyAnalysis(
                            EEG.filterData(
                                EEG.ICA(self.data["openvibeSignal"][key]), fs
                            ),
                            fs,
                        )
                columns, temp_list = [], []
                for channel in EEG_dict.keys():
                    for band in EEG_dict[channel].keys():
                        columns.append(channel + "_" + band)
                        temp_list.append(EEG_dict[channel][band])
                EEG_Dataframe = pd.DataFrame(columns=columns)
                EEG_Dataframe.loc[0] = temp_list
                self.features = pd.concat([EEG_Dataframe, self.features], axis=1)
                # print(EEG_Dataframe)
                # print(self.features)
        return self.features

    def processData(self):
        self.features = pd.DataFrame()

        if "OpenSignals" in self.data.keys():
            self.features = self.getOpenSignals()
        if "openvibeSignal" in self.data.keys():
            self.features = self.getOpenvibe()

        return self.features

    def loadModels(self, path: str, target=""):
        imp = pickle.load(open(path + "\\imp" + target + ".pkl", "rb"))
        scaler = pickle.load(open(path + "\\scaler" + target + ".pkl", "rb"))
        rfe = pickle.load(open(path + "\\rfe" + target + ".pkl", "rb"))
        model = pickle.load(open(path + "\\model" + target + ".pkl", "rb"))

        return imp, scaler, rfe, model

    def predict(self, imp, scaler, rfe, model):
        X = np.array(self.features)
        X = imp.transform(X)
        X = scaler.transform(X)
        X = rfe.transform(X)

        prediction = model.predict(X)

        return prediction
