import pickle

from Signals_Processing import *


class Processing:
    def __init__(self):
        self.info = []
        self.data = {}

    def getOpenSignals(self):
        """

        :return:
        :rtype:
        """

        dataframe, HRV_Dataframe, EDA_Dataframe, RESP_Dataframe = None, None, None, None

        for stream in self.info:
            if stream["Name"] == "OpenSignals":
                name = stream["Name"]
                fs = stream["Sampling Rate"]
                for key in self.data[name].keys():
                    if key.startswith("ECG"):
                        HRV_Dataframe = Process_HRV(self.data[name][key], fs, 16)
                    if key.startswith("EDA"):
                        EDA_Dataframe = Process_EDA(self.data[name][key], fs, 16)
                    if key.startswith("RESP"):
                        RESP_Dataframe = Process_RESP(self.data[name][key], fs, 16)

                dataframe = (HRV_Dataframe.join(EDA_Dataframe)).join(RESP_Dataframe)
                # dataframe = RESP_Dataframe["AVG"]

        return dataframe

    def getOpenvibe(self):
        """

        :return:
        :rtype:
        """
        for stream in self.info:
            if stream["Name"] == "openvibeSignal":
                fs = stream["Sampling Rate"]
                name = stream["Name"]
                EEG_dict = {}
                for i, key in enumerate(self.data[name]):
                    if i > 0 and i < 33:
                        channel = "EEG_" + str(i)
                        EEG_dict[channel] = EEG.frequencyAnalysis(
                            EEG.filterData(EEG.ICA(self.data[name][key]), fs),
                            fs,
                        )

                columns, temp_list = [], []
                for channel in EEG_dict.keys():
                    for band in EEG_dict[channel].keys():
                        columns.append(channel + "_" + band)
                        temp_list.append(EEG_dict[channel][band])
                EEG_Dataframe = pd.DataFrame(columns=columns)
                EEG_Dataframe.loc[0] = temp_list

        return EEG_Dataframe

    def processData(self):
        """

        :return:
        :rtype:
        """
        # print("Process")
        self.features = pd.DataFrame()
        if "OpenSignals" in self.data.keys():
            dataframe = self.getOpenSignals()
        # if "openvibeSignal" in self.data.keys():
        #     EEG_dataframe = self.getOpenvibe()

        # self.features = pd.concat([EEG_dataframe, dataframe], axis=1)
        self.features = dataframe

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
