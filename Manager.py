import csv
import multiprocessing
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
        self.baseline = None
        self.model = None
        self.model_version = 1
        self.model_lock = multiprocessing.Lock()

    def run(self):
        """ """
        # Instantiate object from class Sync and Processing
        sync = Sync(buffer_window=30)
        process = Processing()
        modelTrainer = ModelTrainer()

        folder = os.path.join(os.getcwd(), "Models")
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
                        path + "\\full_dataframe.csv", sep=";", index_col=False
                    )
                    self.training_df = self.training_df.drop("Unnamed: 0", axis=1)
                    print(self.training_df)
                    print("Training Dataframe loaded successfully.\n")
                except Exception as e:
                    print(f"Error loading training dataframe: {e}.")
                try:
                    self.baseline = pd.read_csv(
                        path + "\\Baseline\\df_baseline.csv",
                        sep=";",
                        index_col=False,
                    )
                    self.baseline = self.baseline.drop("Unnamed: 0", axis=1)
                    print("Baseline Dataframe loaded successfully.\n")
                    print(self.baseline)
                except Exception as e:
                    print(f"Error loading baseline dataframe: {e}.")
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
        modelTrainer.start()
        sync.startAcquisition.value = 1
        modelTrainer.startAcquisition.value = 1
        sync.sendBuffer.value = 1

        print("Acquisition Started!")

        i = 0
        previous_df = None

        br, markers = [], []
        video = ""

        # Get streams information
        process.info = sync.info_queue.get()

        try:
            data_sender = DataSender(
                stream_name="biosignalsplux",
                stream_type="stress",
                channel_count=2,
                sampling_rate=IRREGULAR_RATE,
                channel_format=cf_string,
                source_id="id1",
                data_queue=self.data_queue,
                delta_time=1,
            )
            data_sender.start()
            with modelTrainer.lock:
                print("Sending Initial Model and Training Dataframe to Model Trainer.")
                modelTrainer.model_queue.put((self.model, self.training_df))

            # While it is acquiring data
            while bool(sync.startAcquisition.value):
                isDataAvailable = sync.data_available_event.wait(timeout=0.1)
                isModelRetrained = modelTrainer.model_retrained_event.wait(timeout=0.1)

                if isDataAvailable:
                    if sync.data_train_queue.qsize() > 0:
                        with sync.train_lock:
                            data_to_train = sync.data_train_queue.get()

                            # print(data_to_train)
                            print("Getting Training Data from Sync Queue.")
                            new_sample = process.getOpenSignals(
                                data_to_train, process.info
                            )
                            new_sample_label = self.model.predict(np.array(new_sample))[
                                0
                            ]
                            # new_sample["Arousal"] = new_sample_label
                            new_sample["Arousal"] = "Low"
                            print(new_sample)

                            sync.data_available_event.clear()

                            with modelTrainer.lock:
                                modelTrainer.new_sample_queue.put(new_sample)
                                modelTrainer.sample_available_event.set()
                                # print("Sending new data to Model Trainer Queue.")

                if isModelRetrained:
                    with self.model_lock:
                        if not modelTrainer.model_queue.empty():
                            self.model = modelTrainer.model_queue.get()
                            self.model_version += 1
                            # print(self.model)
                            print("Updating retrained model.")
                            modelTrainer.model_retrained_event.clear()

                # If there is data in the buffer queue from Sync, send to Process.
                if sync.buffer_queue.qsize() > 0:
                    sync.sendBuffer.value = 0
                    with sync.lock:
                        # print("Manager has lock.")
                        process.data = sync.buffer_queue.get()
                        i += 1
                        features = process.processData()
                        process.features = features - self.baseline
                        # print(process.features)
                        if previous_df is not None and features is not None:
                            if not np.allclose(
                                features.values, previous_df.values, atol=1e-3
                            ):
                                with self.model_lock:
                                    predicted_sample, probability = process.predict(
                                        self.model
                                    )
                                    self.data_queue.put(
                                        [predicted_sample[0], str(probability)]
                                    )
                                    print(
                                        f"Prediction = {predicted_sample[0]}, Probability = {probability}, Model v{self.model_version}."
                                    )

                        sync.sendBuffer.value = 1
                        previous_df = features

        except Exception as e:
            print(e)
        finally:
            # for i in range(len(br)):
            #     writer.writerow([markers[i], br[i]])
            f.close()
            print("File Closed")
            sync.terminate()
            sync.join()
            modelTrainer.terminate()
            modelTrainer.join()
            data_sender.terminate()
            data_sender.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
