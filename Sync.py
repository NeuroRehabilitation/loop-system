from ReceiveStreams import *
import pandas as pd


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
        for i in range(1, stream_info["Channels"]):
            columns_labels.append("CH" + str(i))
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
                for i in range(1, len(dataframes_dict[stream_name].keys())):
                    column = "CH" + str(i)
                    dataframes_dict[stream_name][column].append(data[0][i])
            if stream_name == "openvibeSignal":
                pass
                # dataframes_dict[stream_name]["Timestamps"].append(data[1])
                # for i in range(1, len(dataframes_dict[stream_name].keys())):
                #     column = "CH" + str(i)
                #     dataframes_dict[stream_name][column].append(data[0][i])
                # dataframes_dict[stream_name]["CH0"].append(data[0][0])
        # print(len(dataframes_dict["openvibeSignal"]["Timestamps"]),len(dataframes_dict["openvibeSignal"]["CH0"]))

if __name__ == "__main__":
    sync = Sync()
    sync.start()
    sync.join()
