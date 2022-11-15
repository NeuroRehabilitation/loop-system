import multiprocessing

from Sync import *
from Process import *
import time


class Manager:
    def run(self):
        sync = Sync(buffer_window=15)
        process = Processing()
        sync.start()
        sync.startAcquisition.value = 1

        process.info = sync.info_queue.get()

        start_time = time.perf_counter()

        while bool(sync.startAcquisition.value):

            elapsed_time = time.perf_counter() - start_time

            if sync.buffer_queue.qsize() > 0:
                process.data = sync.buffer_queue.get()
                process.processData()

            if elapsed_time >= 120:
                sync.startAcquisition.value = 0

        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
