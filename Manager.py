import pandas as pd

from Sync import *
from Process import *
import warnings
import csv

warnings.filterwarnings("ignore")


class Manager(multiprocessing.Process):
    def run(self):
        """ """
        folder = os.getcwd() + "\\Training Models\\"
        participant = "P0"
        path = folder + participant

        try:
            f = open(path + "\\output.csv", "w", newline="")
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
        i = 0

        variable, predictions, true_label = [], [], []

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
        current_features_df = pd.DataFrame(columns=dataframe_baseline.columns)
        final_features_df = pd.DataFrame(columns=dataframe_baseline.columns)

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
                    arousal = process.predict(
                        imp_arousal, scaler_arousal, rfe_arousal, model_arousal
                    )
                    variable.append("Arousal")
                    true_label.append(str(true_arousal))
                    predictions.append(arousal[0])
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

                    variable.append("Valence")
                    true_label.append(str(true_valence))
                    predictions.append(valence[0])
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
                    i += 1
                    process.features = process.processData()
                    current_features_df.loc[i] = process.features.loc[0]

                    process.features = process.features.sub(dataframe_baseline)
                    final_features_df.loc[i] = process.features.loc[0]

                    # category = process.predict(imp, scaler, rfe, model)
                    # arousal = process.predict(
                    #     imp_arousal, scaler_arousal, rfe_arousal, model_arousal
                    # )
                    # valence = process.predict(
                    #     imp_valence, scaler_valence, rfe_valence, model_valence
                    # )

                    if video != "end":
                        if len(video.split("/")) > 1:

                            category = process.predict(imp, scaler, rfe, model)

                            variable.append("Category")
                            true_label.append(video.split("/")[1])
                            predictions.append(category[0])

                            print(
                                "True Category = "
                                + str(video)
                                + " , Category Prediction = "
                                + category
                            )
                        else:
                            arousal = process.predict(
                                imp_arousal, scaler_arousal, rfe_arousal, model_arousal
                            )
                            valence = process.predict(
                                imp_valence, scaler_valence, rfe_valence, model_valence
                            )

                            variable.append("Valence")
                            true_label.append(video)
                            predictions.append(valence[0])

                            variable.append("Arousal")
                            true_label.append(video)
                            predictions.append(arousal[0])

                            print("Valence Prediction = " + str(valence))
                            print("Arousal Prediction = " + str(arousal))

                    sync.sendBuffer.value = 1

        except Exception as e:
            print(e)
        finally:
            for i in range(len(variable)):
                writer.writerow([variable[i], true_label[i], predictions[i]])

            current_features_df.to_csv(
                path + "\\current_features.csv",
                index=False,
                header=True,
            )
            final_features_df.to_csv(
                path + "\\final_features.csv",
                index=False,
                header=True,
            )
            f.close()
            print("File Closed")
            sync.terminate()
            sync.join()


if __name__ == "__main__":
    manager = Manager()
    process = multiprocessing.Process(target=manager.run())
    process.start()
    process.join()
