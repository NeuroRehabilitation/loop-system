import numpy as np
import pandas as pd

from Sync import *
from Process import *
import warnings
import csv

warnings.filterwarnings("ignore")


class Manager(multiprocessing.Process):
    def run(self):
        """ """
        folder = os.getcwd() + "\\Breathing Rate\\"
        participant = "P0"
        path = folder + participant

        info = StreamInfo("biosignalsplux", "Breathing Rate", 1, 1, cf_float32, "id1")

        info_channels = info.desc().append_child("channels")

        info_channels.append_child("channel").append_child_value("label", "BR")

        try:
            f = open(path + "\\output.csv", "w", newline="")
            writer = csv.writer(f)
            header = ["Marker", "Breathing Rate"]
            writer.writerow(header)
        except Exception as e:
            print(e)
        # header = ["Variable", "True Value", "Prediction"]

        # Instantiate object from class Sync and Processing
        sync = Sync(buffer_window=30)
        process = Processing()

        # Start process Sync and put flag startAcquisition as True
        sync.start()
        sync.startAcquisition.value = 1
        sync.sendBuffer.value = 1
        i = 0

        br, markers = [], []

        # Get streams information
        process.info = sync.info_queue.get()

        try:
            outlet_stream = StreamOutlet(info)

            # While is acquiring data
            while bool(sync.startAcquisition.value):
                if sync.markers_queue.qsize() > 0:
                    video, marker = sync.markers_queue.get()
                    print("Video = " + str(video))
                    if video == "end":
                        sync.startAcquisition.value = 0
                # If there is data in the buffer queue from Sync, send to Process.
                if sync.buffer_queue.qsize() > 0:
                    sync.sendBuffer.value = 0
                    process.data = sync.buffer_queue.get()
                    i += 1
                    process.features = process.processData()

                    if not np.isnan(process.features[0]):
                        print(process.features[0])
                        # print(i)
                        outlet_stream.push_sample([process.features[0]])
                        br.append(process.features[0])
                        # markers.append(marker)

                    sync.sendBuffer.value = 1

        except Exception as e:
            print(e)
        finally:
            for i in range(len(br)):
                writer.writerow([markers[i], br[i]])
            f.close()
            print("File Closed")
            sync.terminate()
            sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
