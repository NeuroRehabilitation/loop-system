from lib.sensors import *


class Processing:
    def __init__(self):
        self.info = []
        self.data = {}

    def getOpenSignals(self):
        for stream in self.info:
            if stream["Name"] == "OpenSignals":
                fs = stream["Sampling Rate"]
                for key in self.data["OpenSignals"].keys():
                    if key.startswith("ECG"):
                        sensor = HRV(self.data["OpenSignals"][key], fs, 16)
                        (
                            heart_rate_features,
                            time_features,
                            poincare_features,
                            frequency_features,
                        ) = sensor.getFeatures()
                        print("ECG")
                        print(
                            heart_rate_features,
                            time_features,
                            poincare_features,
                            frequency_features,
                        )
                    elif key.startswith("EDA"):
                        sensor = EDA(self.data["OpenSignals"][key], fs, 16)
                        (
                            eda_phasic_dict,
                            eda_tonic_dict,
                            SCR_Amplitude_dict,
                            SCR_RiseTime_dict,
                            SCR_RecoveryTime_dict,
                            frequency_features,
                        ) = sensor.getFeatures()
                        print("EDA")
                        print(
                            eda_phasic_dict,
                            eda_tonic_dict,
                            SCR_Amplitude_dict,
                            SCR_RiseTime_dict,
                            SCR_RecoveryTime_dict,
                            frequency_features,
                        )
                    elif key.startswith("RESP"):
                        sensor = RESP(self.data["OpenSignals"][key], fs, 16)
                        signals, info = sensor.process_RESP()
                        rrv = sensor.RESP_RRV(signals)
                        df = sensor.getFeatures(signals, rrv)
                        df = df.drop(
                            [
                                "RRV_VLF",
                                "RRV_LF",
                                "RRV_LFHF",
                                "RRV_LFn",
                                "RRV_HFn",
                                "RRV_SD2",
                                "RRV_SD2SD1",
                            ],
                            axis=1,
                        )
                        print("RESP")
                        print(df)
                    elif key.startswith("TEMP"):
                        sensor = TEMP(self.data["OpenSignals"][key], fs, 16)
                        temp = sensor.getFeatures()
                        print(temp)

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
                print(EEG_dict)

    def processData(self):
        if "OpenSignals" in self.data.keys():
            self.getOpenSignals()
        if "openvibeSignal" in self.data.keys():
            self.getOpenvibe()
