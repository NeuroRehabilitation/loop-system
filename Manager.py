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
                # Process ECG
            if key.startswith("EDA"):
                print("EDA")
                # Process EDA
            if key.startswith("RESP"):
                print("RESP")
                # Process EDA
            if key.startswith("TEMP"):
                print("SKT")
                # Process EDA
            if key.startswith("fNIRS"):
                print("fNIRS")
                # Process EDA

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

                if "OpenSignals" in self.data.keys():
                    self.getOpenSignals()
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
