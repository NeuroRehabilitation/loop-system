import csv
from Process import *
from DataSender import *

warnings.filterwarnings("ignore")


class Manager(multiprocessing.Process):
    def __init__(self):
        self.outlet_stream = None
        self.data_to_stream = None
        self.data_queue = multiprocessing.Queue()

    def run(self):
        """ """
        folder = os.getcwd() + "\\Breathing Rate\\"
        participant = "P0"
        path = folder + participant

        try:
            f = open(path + "\\output.csv", "w", newline="")
            writer = csv.writer(f)
            header = ["Variable", "Value"]
            writer.writerow(header)
        except Exception as e:
            print(e)

        # Instantiate object from class Sync and Processing
        sync = Sync(buffer_window=40)
        process = Processing()

        # Start process Sync and put flag startAcquisition as True
        sync.start()
        sync.startAcquisition.value = 1
        sync.sendBuffer.value = 1
        i = 0

        br, markers = [], []
        video = ""

        # Get streams information
        process.info = sync.info_queue.get()

        try:
            data_sender = DataSender(
                stream_name="biosignalsplux",
                stream_type="Breathing Rate",
                channel_count=1,
                sampling_rate=IRREGULAR_RATE,
                channel_format=cf_float32,
                source_id="id1",
                data_queue=self.data_queue,
                delta_time=5,
            )
            data_sender.start()
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
                        self.data_queue.put(process.features[0])
                        print(process.features[0])
                        br.append(process.features[0])
                        markers.append(video)

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
            data_sender.terminate()
            data_sender.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
