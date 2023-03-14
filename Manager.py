from Sync import *
from Process import *
import time


class Manager:
    def run(self):
        # Instantiate object from class Sync and Processing
        sync = Sync(buffer_window=40)
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
            if sync.markers_queue.qsize() > 0:
                video, marker = sync.markers_queue.get()
                print("Video = " + str(video))
                if video == "end":
                    sync.startAcquisition.value = 0
                if video == "start":
                    sync.videoStarted.value = 1
            if sync.arousal_queue.qsize() > 0:
                arousal = sync.arousal_queue.get()
                print("Arousal = " + str(arousal))
            if sync.valence_queue.qsize() > 0:
                valence = sync.valence_queue.get()
                print("Valence = " + str(valence))
            # If there is data in the buffer queue from Sync, send to Process.
            if sync.buffer_queue.qsize() > 0:
                process.data = sync.buffer_queue.get()
                process.features = process.processData()
                print(process.features)

            # Set end of acquisition in seconds and put flag startAcquisition as False.

        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
