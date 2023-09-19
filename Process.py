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
                try:
                    for key in self.data[name].keys():
                        if key.startswith("ECG"):
                            try:
                                HRV_Dataframe = Process_HRV(
                                    self.data[name][key], fs, 16
                                )
                                self.features = pd.concat(
                                    [self.features, HRV_Dataframe], axis=1
                                )
                            except Exception as e:
                                print(e)
                                print("Error on HRV Dataframe!")

                        elif key.startswith("EDA"):
                            try:
                                EDA_Dataframe = Process_EDA(
                                    self.data[name][key], fs, 16
                                )
                                self.features = pd.concat(
                                    [self.features, EDA_Dataframe], axis=1
                                )
                            except Exception as e:
                                print(e)
                                print("Error on EDA Dataframe!")

                        elif key.startswith("RESP"):
                            try:
                                RESP_Dataframe = Process_RESP(
                                    self.data[name][key], fs, 16
                                )
                                self.features = pd.concat(
                                    [self.features, RESP_Dataframe], axis=1
                                )
                            except Exception as e:
                                print(e)
                except Exception as e:
                    print(e)
                finally:
                    return self.features

    def getOpenvibe(self):
        for stream in self.info:
            if stream["Name"] == "openvibeSignal":
                try:
                    fs = stream["Sampling Rate"]

                    EEG_dict = {}
                    for i, key in enumerate(self.data["openvibeSignal"]):
                        try:
                            if i > 0 and i < 33:
                                channel = "EEG_" + str(i)
                                EEG_dict[channel] = EEG.frequencyAnalysis(
                                    EEG.filterData(
                                        EEG.ICA(self.data["openvibeSignal"][key]), fs
                                    ),
                                    fs,
                                )
                        except Exception as e:
                            print(e)
                    columns, temp_list = [], []
                    for channel in EEG_dict.keys():
                        for band in EEG_dict[channel].keys():
                            columns.append(channel + "_" + band)
                            temp_list.append(EEG_dict[channel][band])
                    EEG_Dataframe = pd.DataFrame(columns=columns)
                    EEG_Dataframe.loc[0] = temp_list
                    try:
                        self.features = pd.concat(
                            [EEG_Dataframe, self.features], axis=1
                        )
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e)
                finally:
                    return self.features

    def processData(self):
        self.features = pd.DataFrame()
        try:
            if "OpenSignals" in self.data.keys():
                self.features = self.getOpenSignals()
        except Exception as e:
            print(e)
            print("OpenSignals Error!")
        try:
            if "openvibeSignal" in self.data.keys():
                self.features = self.getOpenvibe()
        except Exception as e:
            print(e)
            print("Openvibe Error!")

        return self.features

    def loadModels(self, path: str, target=""):
        try:
            imp = pickle.load(open(path + "\\imp" + target + ".pkl", "rb"))
        except Exception as e:
            print(e)
            print("Error on loading Imputer file!")
        try:
            scaler = pickle.load(open(path + "\\scaler" + target + ".pkl", "rb"))
        except Exception as e:
            print(e)
            print("Error on loading Scaler file!")
        try:
            rfe = pickle.load(open(path + "\\rfe" + target + ".pkl", "rb"))
        except Exception as e:
            print(e)
            print("Error on loading RFE file!")
        try:
            model = pickle.load(open(path + "\\model" + target + ".pkl", "rb"))
        except Exception as e:
            print(e)
            print("Error on loading Model file!")

        return imp, scaler, rfe, model

    def predict(self, imp, scaler, rfe, model):
        try:
            X = np.array(self.features)
            if len(X) > 0:
                X = imp.transform(X)
                X = scaler.transform(X)
                X = rfe.transform(X)

                prediction = model.predict(X)

                return prediction
            else:
                print("X has no data!")
        except Exception as e:
            print(e)
            print("No prediction")
