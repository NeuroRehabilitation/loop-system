import csv
import os.path
import sys
import time
from io import StringIO
from DataSender import *
from ModelTrainer import *
from Process import *

warnings.filterwarnings("ignore")


class Manager(multiprocessing.Process):
    def __init__(self):
        self.outlet_stream = None
        self.data_to_stream = None
        self.data_queue = multiprocessing.Queue()
        self.training_df = None
        self.model = None

    def run(self):
        """ """
        # Instantiate object from class Sync and Processing
        sync = Sync(buffer_window=60)
        process = Processing()
        modelTrainer = ModelTrainer()

        folder = os.path.join(os.getcwd(), "Breathing Rate")
        participant = input("Enter the participant ID (e.g., P0): ").strip()

        if participant:
            path = os.path.join(folder, participant)

            if not os.path.exists(path):
                raise FileNotFoundError(f"The directory {path} does not exist.")
                sys.exit(1)
            else:
                try:
                    with open(path + "\\output.csv", "w", newline="") as f:
                        writer = csv.writer(f)
                        header = ["Variable", "Value"]
                        writer.writerow(header)
                    print("Output file created successfully.")
                except Exception as e:
                    print(f"An error occurred: {e}.")
                try:
                    self.training_df = pd.read_csv(
                        path + "\\sr_dataframe.csv", sep=",", index_col=False
                    )
                except Exception as e:
                    print(f"Error loading training dataframe: {e}.")
                try:
                    self.model = process.loadModel(path)
                except Exception as e:
                    print(f"Error loading model: {e}.")
        else:
            print("No participant ID provided. Exiting...")
            sys.exit(1)

        input("Press Enter to start acquisition...")

        # Start process Sync and put flag startAcquisition as True
        sync.start()
        sync.startAcquisition.value = 1
        sync.sendBuffer.value = 1

        print("Acquisition Started!")

        i = 0
        previous_value = 0

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
            start_time = time.time()

            # While it is acquiring data
            while bool(sync.startAcquisition.value):
                elapsed = time.time() - start_time
                # sys.stdout.write(f"\rElapsed Time: {elapsed:.2f} seconds")
                sys.stdout.write(f"\r Queue size = {sync.buffer_queue.qsize()}")
                sys.stdout.flush()
                time.sleep(0.1)  # Update every 100 ms
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

                    if (
                        not np.isnan(process.features[0])
                        and process.features[0] != previous_value
                    ):
                        self.data_queue.put(process.features[0])
                        print(process.features[0])
                        previous_value = process.features[0]
                        # br.append(process.features[0])
                        # markers.append(video)

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
