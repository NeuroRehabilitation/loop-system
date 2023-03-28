from Sync import *
from Process import *


class Manager:
    def run(self):

        folder = os.getcwd() + "\\Training Models\\"
        participant = "P2"
        path = folder + participant

        # Instantiate object from class Sync and Processing
        sync = Sync(buffer_window=40)
        process = Processing()

        # Start process Sync and put flag startAcquisition as True
        sync.start()
        sync.startAcquisition.value = 1

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
                    print("end")
                    sync.startAcquisition.value = 0
                if video == "start":
                    sync.startBuffer.value = 1
            if sync.arousal_queue.qsize() > 0:
                true_arousal = sync.arousal_queue.get()
                arousal = process.predict(
                    imp_arousal, scaler_arousal, rfe_arousal, model_arousal
                )
                print("Arousal Prediction = " + str(arousal))
            if sync.valence_queue.qsize() > 0:
                true_valence = sync.valence_queue.get()
                print("Valence = " + str(true_valence))
                valence = process.predict(
                    imp_valence, scaler_valence, rfe_valence, model_valence
                )
                print("Valence Prediction = " + str(valence))
            # If there is data in the buffer queue from Sync, send to Process.
            if sync.buffer_queue.qsize() > 0:
                process.data = sync.buffer_queue.get()
                process.features = process.processData()
                process.features -= dataframe_baseline
                # print(process.features)
                category = process.predict(imp, scaler, rfe, model)
                # print(category)

        sync.terminate()
        sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
