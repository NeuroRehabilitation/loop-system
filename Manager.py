from Sync import *
import time
import matplotlib.pyplot as plt
from lib.sensors import *


class Manager:
    def __init__(self):
        super().__init__()
        self.data = {}
        self.info = []

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
                    if key.startswith("EDA"):
                        sensor = EDA(self.data["OpenSignals"][key], fs, 16)
                        (
                            eda_phasic_dict,
                            eda_tonic_dict,
                            SCR_Amplitude_dict,
                            SCR_RiseTime_dict,
                            SCR_RecoveryTime_dict,
                            frequency_features,
                        ) = sensor.getFeatures()
                    if key.startswith("RESP"):
                        sensor = RESP(self.data["OpenSignals"][key], fs, 16)
                        signals, info = sensor.process_RESP()
                    if key.startswith("TEMP"):
                        sensor = TEMP(self.data["OpenSignals"][key], fs, 16)
                        temp = sensor.getFeatures()

    def run(self):
        sync = Sync(buffer_window=15)
        sync.start()
        sync.startAcquisition.value = 1

        self.info = sync.info_queue.get()

        start_time = time.perf_counter()

        while bool(sync.startAcquisition.value):
            elapsed_time = time.perf_counter() - start_time
            if sync.buffer_queue.qsize() > 0:
                self.data = sync.buffer_queue.get()

                if "OpenSignals" in self.data.keys():
                    self.getOpenSignals()

            if elapsed_time >= 30:
                sync.startAcquisition.value = 0

        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
