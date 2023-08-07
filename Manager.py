from Sync import *
from Process import *
import warnings
import csv

warnings.filterwarnings("ignore")


class Manager:
    def run(self):
        folder = os.getcwd() + "\\Training Models\\"
        participant = "P0"
        path = folder + participant

        f = open(path + "\\output.csv", "w")
        writer = csv.writer(f)
        header = ["Variable", "True Value", "Prediction"]
        writer.writerow(header)

        # Instantiate object from class Sync and Processing
        sync = Sync(buffer_window=40)
        process = Processing()

        # Start process Sync and put flag startAcquisition as True
        sync.start()
        sync.startAcquisition.value = 1
        sync.sendBuffer.value = 1

        imp, scaler, rfe, model = process.loadModels(path)
        imp_arousal, scaler_arousal, rfe_arousal, model_arousal = process.loadModels(
            path, target="_arousal"
        )
        imp_valence, scaler_valence, rfe_valence, model_valence = process.loadModels(
            path, target="_valence"
        )

        EEGbaseline = pd.read_csv(path + "\\EEGbaseline.csv", sep=";", index_col=0)
        baseline = pd.read_csv(path + "\\baseline.csv", sep=";", index_col=0)

        dataframe_baseline = pd.concat([EEGbaseline, baseline], axis=1)
        # Get streams information
        process.info = sync.info_queue.get()

        # While is acquiring data
        while bool(sync.startAcquisition.value):
            if sync.markers_queue.qsize() > 0:
                video, marker = sync.markers_queue.get()
                print("Video = " + str(video))
                if video == "end":
                    sync.startAcquisition.value = 0
            if sync.arousal_queue.qsize() > 0:
                true_arousal = sync.arousal_queue.get()
                arousal = process.predict(
                    imp_arousal, scaler_arousal, rfe_arousal, model_arousal
                )
                writer.writerow(["Arousal", str(true_arousal), arousal[0]])
                print(
                    "True Arousal = "
                    + str(true_arousal)
                    + " , Arousal Prediction = "
                    + str(arousal)
                )
            if sync.valence_queue.qsize() > 0:
                true_valence = sync.valence_queue.get()
                valence = process.predict(
                    imp_valence, scaler_valence, rfe_valence, model_valence
                )
                writer.writerow(["Valence", str(true_valence), valence[0]])
                print(
                    "True Valence = "
                    + str(true_valence)
                    + " , Valence Prediction = "
                    + str(valence)
                )
            # If there is data in the buffer queue from Sync, send to Process.
            if sync.buffer_queue.qsize() > 0:
                sync.sendBuffer.value = 0
                process.data = sync.buffer_queue.get()
                process.features = process.processData()
                process.features = process.features.sub(dataframe_baseline)
                category = process.predict(imp, scaler, rfe, model)
                if video != "end":
                    writer.writerow(["Category", video.split("/")[1], category[0]])
                print(
                    "True Category = "
                    + str(video)
                    + " , Category Prediction = "
                    + category
                )
                sync.sendBuffer.value = 1

        f.close()
        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
