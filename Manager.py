from Sync import *
import time
import matplotlib.pyplot as plt


class Manager(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.data = {}

    def run(self):

        sync = Sync(buffer_window=20)
        sync.start()
        sync.startAcquisition.value = 1

        start_time = time.perf_counter()

        while bool(sync.startAcquisition.value):
            elapsed_time = time.perf_counter() - start_time
            if sync.buffer_queue.qsize() > 0:
                self.data = sync.buffer_queue.get()
                print(self.data.keys())

            if elapsed_time >= 30:
                sync.startAcquisition.value = 0
                plt.figure()
                plt.plot(self.data["OpenSignals"]["RAW0"])
                plt.show()

        # plt.figure()
        # plt.plot(sync.synced_dict["OpenSignals"]["RAW0"])
        # plt.show()
        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    manager.start()
    manager.join()
