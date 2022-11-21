import pandas as pd

from lib.sensors import *
from Process_Features import *


class Processing:
    def __init__(self):
        self.info = []
        self.data = {}
        self.features = pd.DataFrame()

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
                        # print("HRV")
                        # print(HRV_Dataframe)

                    elif key.startswith("EDA"):
                        EDA_Dataframe = Process_EDA(self.data[name][key], fs, 16)
                        self.features = pd.concat(
                            [self.features, EDA_Dataframe], axis=1
                        )
                        # print("EDA")
                        # print(EDA_Dataframe)

                    elif key.startswith("RESP"):
                        RESP_Dataframe = Process_RESP(self.data[name][key], fs, 16)
                        self.features = pd.concat(
                            [self.features, RESP_Dataframe], axis=1
                        )
                        # print("RESP")
                        # print(RESP_Dataframe)

                    elif key.startswith("TEMP"):
                        SKT_Dataframe = Process_TEMP(self.data[name][key], fs, 16)
                        self.features = pd.concat(
                            [self.features, SKT_Dataframe], axis=1
                        )
                        # print("SKT")
                        # print(SKT_Dataframe)

                # print("Features")
                # print(self.features)

    def getOpenvibe(self):
        for stream in self.info:
            if stream["Name"] == "openvibeSignal":
                EEG_dict = {}
                fs = stream["Sampling Rate"]
                for i, key in enumerate(self.data["openvibeSignal"]):
                    if i > 0 and i < 33:
                        channel = "EEG" + str(i)
                        sensor = EEG(self.data["openvibeSignal"][key], fs, 16)
                        EEG_dict[channel] = sensor.getFeatures()

                EEG_Dataframe = pd.DataFrame.from_dict(EEG_dict, orient="index")
                print(EEG_Dataframe)
                self.features = pd.concat([self.features, EEG_Dataframe], axis=1)

    def processData(self):
        if "OpenSignals" in self.data.keys():
            self.getOpenSignals()
        if "openvibeSignal" in self.data.keys():
            self.getOpenvibe()
