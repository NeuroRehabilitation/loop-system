from Sync import *
import time


class Manager(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.data = {}

    def run(self):

        sync = Sync(buffer_window=5)
        sync.start()
        sync.startAcquisition.value = 1

        start_time = time.perf_counter()

        while bool(sync.startAcquisition.value):
            elapsed_time = time.perf_counter() - start_time

            if elapsed_time >= 10:
                sync.startAcquisition.value = 0
        #         # plt.figure()
        #         # plt.plot(sync.synced_dict["OpenSignals"]["RAW0"])
        #         # plt.show()

        # plt.figure()
        # plt.plot(sync.synced_dict["OpenSignals"]["RAW0"])
        # plt.show()
        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    manager.start()
    manager.join()
