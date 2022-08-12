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

    def createDataframe(self, stream_info: dict):
        columns_labels = []
        for i in range(1, stream_info["Channels"]):
            columns_labels.append("CH" + str(i))
        dataframe = pd.DataFrame(columns=columns_labels)

        return dataframe

    def run(self):

        dataframes_dict = {}

        streams_receiver = self.getStreams()
        self.getStreamsInfo(streams_receiver)

        for stream in self.streams_info:
            dataframes_dict[stream["Name"]] = self.createDataframe(stream)

        # self.isRunning = True
        start_time = time.perf_counter()
        elapsed_time = 0

        while elapsed_time < 5:
            elapsed_time = time.perf_counter() - start_time
            print(elapsed_time)
            stream_name = streams_receiver.sender_queue.get()[0]
            if stream_name == "OpenSignals":
                df = pd.DataFrame()
                for i in range(1, len(streams_receiver.sender_queue.get()[1][0][0])):
                    column = "CH" + str(i)
                    df[column] = streams_receiver.sender_queue.get()[1][0][:, i]
                    dataframes_dict[stream_name] = pd.concat(
                        [dataframes_dict[stream_name], df], ignore_index=True
                    )
                    # dataframes_dict[stream_name] = dataframes_dict[stream_name][column].concat(streams_receiver.sender_queue.get()[1][0][:,i],axis=1,ignore_index=True)
        print(dataframes_dict["OpenSignals"])


if __name__ == "__main__":
    sync = Sync()
    sync.start()
    sync.join()
