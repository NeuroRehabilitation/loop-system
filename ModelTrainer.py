import multiprocessing

from DataSender import *
from Process import *

warnings.filterwarnings("ignore")


class ModelTrainer(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        # Queue for communication with Manager
        self.model_queue = multiprocessing.Queue()
        # Flag to check if the process is running
        self.running = False
        # Training Data
        self.training_data = None
        # New Sample Data
        self.new_data = None
        # Placeholder for model
        self.model = None
        # Lock to access queue
        self.lock = multiprocessing.Lock()

        self.startAcquisition = multiprocessing.Value("i", 0)

    @staticmethod
    def is_incremental_model(model):
        """Check if the model supports incremental learning (i.e., has `partial_fit` method)."""
        return hasattr(model, "partial_fit")

    def train_model(self):

        columns = self.training_data.columns[: len(self.training_data.columns) - 1]

        X_train = np.array(self.training_data[columns])
        Y_train = np.array(self.training_data["Arousal"])

        x_sample = self.new_data[0]
        y_sample = self.new_data[1]

        # Add the current sample to the training data
        X_train = np.vstack((X_train, x_sample))  # Add new sample to training features
        Y_train = np.hstack((Y_train, y_sample))

        print("Training Model on new data.")
        # Retrain the model depending on whether it supports incremental learning
        for name, estimator in self.model.named_estimators_.items():
            if self.is_incremental_model(estimator):
                # Use partial_fit for incremental learning models
                estimator.partial_fit(x_sample, y_sample, classes=self.model.classes_)
            else:
                # Re-train from scratch for non-incremental learning models
                estimator.fit(X_train, Y_train)
        print("Model Retrained Successfully!")

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
                if self.model is not None and self.training_data is not None:
                    print("Getting Initial Model and Training from Manager.")
                    self.model, self.training_data = self.model_queue.get()
                else:
                    self.new_data = self.model_queue.get()
                print(f"Model = {self.model}")
                print(f"New Data = {self.new_data}")
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
                self.receive_data()
                self.train_model()
                self.send_model_retrained()
