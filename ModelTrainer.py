import multiprocessing
import time

from DataSender import *
from Process import *

warnings.filterwarnings("ignore")


class ModelTrainer(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        # Queue for communication with Manager
        self.model_queue = multiprocessing.Queue()
        # Flag to check if the process is running
        self.running, self.isTraining = False, False
        # Training Data
        self.training_data = None
        # New Sample Data
        self.new_data = None
        # Placeholder for model
        self.model = None
        # Lock to access queue
        self.lock = multiprocessing.Lock()
        # Flag to start the acquisition of data by the Manager.
        self.startAcquisition = multiprocessing.Value("i", 0)

        self.X_train, self.Y_train = None, None
        self.columns = None

    @staticmethod
    def is_incremental_model(model):
        """Check if the model supports incremental learning (i.e., has `partial_fit` method)."""
        return hasattr(model, "partial_fit")

    def train_model(self):
        start_time = time.time()
        x_sample = np.array(self.new_data[self.columns])
        y_sample = np.array(self.new_data["Arousal"])

        # Add the current sample to the training data
        self.X_train = np.vstack(
            (self.X_train, x_sample)
        )  # Add new sample to training features
        self.Y_train = np.hstack((self.Y_train, y_sample))

        if not self.isTraining:
            self.isTraining = True
            print("Training Model on new data.")
            # Retrain the model depending on whether it supports incremental learning
            for name, estimator in self.model.named_estimators_.items():
                if self.is_incremental_model(estimator):
                    # Use partial_fit for incremental learning models
                    estimator.partial_fit(
                        x_sample, y_sample, classes=self.model.classes_
                    )
                else:
                    # Re-train from scratch for non-incremental learning models
                    estimator.fit(self.X_train, self.Y_train)
            print(
                f"Model Retrained Successfully in {(time.time()-start_time):.2f} seconds!"
            )
            self.isTraining = False

    def start_training(self):
        """Start the training process."""
        if not self.running:
            self.running = True
            print("Model Trainer process started.")
        else:
            print("Model Trainer process is already running.")

    def receive_data(self):
        """Receive model and training data from the Manager."""
        if self.running:
            with self.lock:
                if self.model is None and self.training_data is None:
                    print("Getting Initial Model and Training from Manager.")
                    self.model, self.training_data = self.model_queue.get()
                    self.columns = self.training_data.columns[
                        : len(self.training_data.columns) - 1
                    ]
                    self.X_train = np.array(self.training_data[self.columns])
                    self.Y_train = np.array(self.training_data["Arousal"])
                else:
                    self.new_data = self.model_queue.get()
                    print("Getting new sample to train.")

        else:
            print("Training process is not running. Start the process first.")

    def send_model_retrained(self):
        if self.running:
            with self.lock:
                self.model_queue.put(self.model)
                print("Putting retrained model in Manager Queue.")
        else:
            print("Training process is not running. Start the process first.")

    def run(self):
        self.start_training()
        while bool(self.startAcquisition.value):
            if self.model_queue.qsize() > 0:
                if self.model is None and self.training_data is None:
                    self.receive_data()
                    print(f"Len X_Train = {len(self.X_train)}")
                else:
                    self.receive_data()
                    self.train_model()

                # self.send_model_retrained()