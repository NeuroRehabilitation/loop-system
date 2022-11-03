from Sync import *
import time
import matplotlib.pyplot as plt


class Manager(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.data = {}

    def getOpenSignals(self):
        for key in self.data["OpenSignals"].keys():
            if key.startswith("ECG"):
                print("ECG")
                sensor = HRV(self.data["OpenSignals"][key], 1000, 16)
                (
                    heart_rate,
                    time_features,
                    poincare_features,
                    frequency_features,
                ) = sensor.getFeatures()
                print(f"HR = ".format(heart_rate))
                # Process ECG
            if key.startswith("EDA"):
                print("EDA")
                sensor = EDA(self.data["OpenSignals"][key], 1000, 16)
                (
                    eda_phasic_dict,
                    eda_tonic_dict,
                    SCR_Amplitude_dict,
                    SCR_RiseTime_dict,
                    SCR_RecoveryTime_dict,
                    frequency_features,
                ) = sensor.getFeatures()
                # Process EDA
            if key.startswith("RESP"):
                print("RESP")
                sensor = RESP(self.data["OpenSignals"][key], 1000, 16)
                signals, info = sensor.process_RESP()
                # Process RESP
            if key.startswith("TEMP"):
                print("SKT")
                sensor = TEMP(self.data["OpenSignals"][key], 1000, 16)
                temp = sensor.getFeatures()
                # Process TEMP

    def run(self):
        sync = Sync(buffer_window=45)
        sync.start()
        sync.startAcquisition.value = 1

        start_time = time.perf_counter()

        while bool(sync.startAcquisition.value):
            elapsed_time = time.perf_counter() - start_time
            if sync.buffer_queue.qsize() > 0:
                self.data = sync.buffer_queue.get()
                print(self.data["OpenSignals"].keys())

                # if "OpenSignals" in self.data.keys():
                #     pass
                # self.getOpenSignals()
                # call function getOpenSignals.

            if elapsed_time >= 60:
                sync.startAcquisition.value = 0
                plt.figure()
                plt.plot(self.data["OpenSignals"]["ECGBIT0"])
                plt.plot(self.data["OpenSignals"]["RESPBIT1"])
                plt.show()

        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    manager.start()
    manager.join()
