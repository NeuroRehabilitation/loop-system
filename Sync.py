import time

from ReceiveStreams import *


class Sync(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.data_queue = multiprocessing.Queue()
        self.streams_info = []
        self.isRunning = False

    def getStreams(self):
        streams_receiver = ReceiveStreams()
        streams_receiver.start()

        return streams_receiver

    def getStreamsInfo(self, streams_receiver):
        self.streams_info = streams_receiver.info_queue.get()

    def createDict(self, stream_info: dict):
        columns_labels = ["Timestamps"]
        for key in stream_info["Channels Info"].keys():
            columns_labels.append(stream_info["Channels Info"][key][0])
        dict = {key: [] for key in columns_labels}

        return dict

    def run(self):

        dataframes_dict = {}

        streams_receiver = self.getStreams()
        self.getStreamsInfo(streams_receiver)

        for stream in self.streams_info:
            dataframes_dict[stream["Name"]] = self.createDict(stream)
        # self.isRunning = True
        start_time = time.perf_counter()
        elapsed_time = 0

        while elapsed_time < 5:
            elapsed_time = time.perf_counter() - start_time
            print(elapsed_time)
            stream_name, data = streams_receiver.data_queue.get()
            if stream_name == "OpenSignals":
                dataframes_dict[stream_name]["Timestamps"].append(data[1])
                for i, key in enumerate(dataframes_dict[stream_name].keys()):
                    if key != "Timestamps":
                        dataframes_dict[stream_name][key].append(data[0][i - 1])
            if stream_name == "openvibeSignal":
                dataframes_dict[stream_name]["Timestamps"].append(data[1])
                for i, key in enumerate(dataframes_dict[stream_name].keys()):
                    if key != "Timestamps":
                        dataframes_dict[stream_name][key].append(data[0][i - 1])

        print(
            len(dataframes_dict["OpenSignals"]["Timestamps"]),
            len(dataframes_dict["OpenSignals"]["nSeq"]),
            len(dataframes_dict["OpenSignals"]["RESPBIT0"]),
            len(dataframes_dict["OpenSignals"]["EDABITREV1"]),
            len(dataframes_dict["openvibeSignal"]["Timestamps"]),
            len(dataframes_dict["openvibeSignal"]["Time(s)"]),
        )


if __name__ == "__main__":
    sync = Sync()
    sync.start()
    sync.join()
