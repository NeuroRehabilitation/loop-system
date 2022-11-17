import multiprocessing

from Sync import *
from Process import *
import time


class Manager:
    def run(self):
        # Instantiate object from class Sync and Processing
        sync = Sync(buffer_window=15)
        process = Processing()

        # Start process Sync and put flag startAcquisition as True
        sync.start()
        sync.startAcquisition.value = 1

        # Get streams information
        process.info = sync.info_queue.get()

        # Start timer
        start_time = time.perf_counter()

        # While is acquiring data
        while bool(sync.startAcquisition.value):

            # Update timer
            elapsed_time = time.perf_counter() - start_time

            # If there is data in the buffer queue from Sync, send to Process.
            if sync.buffer_queue.qsize() > 0:
                process.data = sync.buffer_queue.get()
                process.processData()

            # Set end of acquisition in seconds and put flag startAcquisition as False.
            if elapsed_time >= 120:
                sync.startAcquisition.value = 0

        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
