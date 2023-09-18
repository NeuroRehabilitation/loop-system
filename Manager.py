import pandas as pd

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

        try:
            f = open(path + "\\output_test.csv", "w")
        except Exception as e:
            print(e)
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

        previousDataframe = pd.DataFrame()

        try:
            imp, scaler, rfe, model = process.loadModels(path)
        except Exception as e:
            print(e)
            print("Error loading models!")
        try:
            (
                imp_arousal,
                scaler_arousal,
                rfe_arousal,
                model_arousal,
            ) = process.loadModels(path, target="_arousal")
        except Exception as e:
            print(e)
            print("Error loading arousal models!")
        try:
            (
                imp_valence,
                scaler_valence,
                rfe_valence,
                model_valence,
            ) = process.loadModels(path, target="_valence")
        except Exception as e:
            print(e)
            print("Error loading valence models!")

        try:
            EEGbaseline = pd.read_csv(path + "\\EEGbaseline.csv", sep=";", index_col=0)
        except Exception as e:
            print(e)
        try:
            baseline = pd.read_csv(path + "\\baseline.csv", sep=";", index_col=0)
        except Exception as e:
            print(e)

        dataframe_baseline = pd.concat([EEGbaseline, baseline], axis=1)
        # Get streams information
        process.info = sync.info_queue.get()

        # While is acquiring data
        try:
            while bool(sync.startAcquisition.value):
                if sync.markers_queue.qsize() > 0:
                    video, marker = sync.markers_queue.get()
                    print("Video = " + str(video))
                    if video == "end":
                        sync.startAcquisition.value = 0
                if sync.arousal_queue.qsize() > 0:
                    true_arousal = sync.arousal_queue.get()
                    try:
                        arousal = process.predict(
                            imp_arousal, scaler_arousal, rfe_arousal, model_arousal
                        )
                    except Exception as e:
                        print(e)
                        pass
                    else:
                        writer.writerow(["Arousal", str(true_arousal), arousal[0]])
                        print(
                            "True Arousal = "
                            + str(true_arousal)
                            + " , Arousal Prediction = "
                            + str(arousal)
                        )
                if sync.valence_queue.qsize() > 0:
                    true_valence = sync.valence_queue.get()
                    try:
                        valence = process.predict(
                            imp_valence, scaler_valence, rfe_valence, model_valence
                        )
                    except Exception as e:
                        print(e)
                        pass
                    else:
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
                    print(process.features)
                    category = process.predict(imp, scaler, rfe, model)
                    arousal = process.predict(
                        imp_arousal, scaler_arousal, rfe_arousal, model_arousal
                    )
                    valence = process.predict(
                        imp_valence, scaler_valence, rfe_valence, model_valence
                    )
                    if video != "end":
                        if len(video.split("/")) > 1:
                            # writer.writerow(
                            #     ["Category", video.split("/")[1], category[0]]
                            # )
                            pass
                        else:
                            # writer.writerow([video, "Valence", valence[0]])
                            # writer.writerow([video, "Arousal", arousal[0]])
                            pass
                    print(
                        "True Category = "
                        + str(video)
                        + " , Category Prediction = "
                        + category
                    )
                    # print("Valence Prediction = " + str(valence))
                    # print("Arousal Prediction = " + str(arousal))
                    sync.sendBuffer.value = 1
        except Exception as e:
            print(e)
        finally:
            f.close()
            print("File Closed")
            sync.terminate()
            sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
