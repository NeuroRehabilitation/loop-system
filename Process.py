from lib.sensors import *
from Process_Features import *


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
                        print(HRV_Dataframe)

                    elif key.startswith("EDA"):
                        EDA_Dataframe = Process_EDA(self.data[name][key], fs, 16)
                        print(EDA_Dataframe)

                    elif key.startswith("RESP"):
                        RESP_Dataframe = Process_RESP(self.data[name][key], fs, 16)
                        print(RESP_Dataframe)

                    elif key.startswith("TEMP"):
                        SKT_Dataframe = Process_TEMP(self.data[name][key], fs, 16)
                        print(SKT_Dataframe)

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

    def processData(self):
        if "OpenSignals" in self.data.keys():
            self.getOpenSignals()
        if "openvibeSignal" in self.data.keys():
            self.getOpenvibe()
