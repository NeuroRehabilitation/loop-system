import time
import matplotlib.pyplot as plt
from ReceiveStreams import *


class Sync(multiprocessing.Process):
    def __init__(self, buffer_window: int):
        super().__init__()
        self.data_queue = multiprocessing.Queue()
        self.streams_info, self.childProcesses = [], []
        self.synced_dict, self.info_dict, self.timestamps = {}, {}, {}
        self.isSync, self.isFirstBuffer = False, True
        self.n_full_buffers = 0
        self.buffer_window = buffer_window

    def getStreams(self):
        streams_receiver = ReceiveStreams()
        streams_receiver.start()

        return streams_receiver

    def getStreamsInfo(self, streams_receiver) -> None:
        self.streams_info = streams_receiver.info_queue.get()

    def createDict(self, stream_info: dict) -> dict:
        columns_labels = ["Timestamps"]
        for key in stream_info["Channels Info"].keys():
            print(stream_info["Channels Info"][key][0])
            columns_labels.append(stream_info["Channels Info"][key][0])
        dict = {key: [] for key in columns_labels}

        return dict

    def fillData(self, data: tuple, stream_name: str) -> None:
        self.synced_dict[stream_name]["Timestamps"].append(data[1])
        for i, key in enumerate(self.synced_dict[stream_name].keys()):
            if key != "Timestamps":
                self.synced_dict[stream_name][key].append(data[0][i - 1])

    def getBufferMaxSize(self, stream_name: str) -> int:
        return int(self.buffer_window * self.info_dict[stream_name]["Sampling Rate"])

    def checkBufferSize(self, data: tuple, max_size: int, stream_name: str):
        if not self.info_dict[stream_name]["All arrays full"]:
            if self.info_dict[stream_name]["Number full arrays"] == len(
                self.synced_dict[stream_name].keys()
            ):
                self.info_dict[stream_name]["All arrays full"] = True
                self.n_full_buffers += 1
            else:
                for key in self.synced_dict[stream_name].keys():
                    if len(self.synced_dict[stream_name][key]) == max_size:
                        self.info_dict[stream_name]["Number full arrays"] += 1
                    if len(self.synced_dict[stream_name][key]) < max_size:
                        self.fillData(data, stream_name)

    def slidingWindow(self, stream_name: str):
        for key in self.synced_dict[stream_name].keys():
            self.synced_dict[stream_name][key].pop(0)

    def syncStreams(self, first_timestamp: int) -> None:
        if first_timestamp == 0 and len(self.timestamps.values()) > 1:
            first_timestamp = min(self.timestamps.values())
        if first_timestamp != 0:
            if all(i >= first_timestamp for i in self.timestamps.values()):
                self.isSync = True
                print("Streams are Synced.")

    def getBuffers(self, data: tuple, stream_name: str):
        if not self.isSync:
            self.timestamps[stream_name] = data[1]
        else:
            if self.isFirstBuffer:
                if self.n_full_buffers == len(self.synced_dict.keys()):
                    print("All arrays full")
                    print(
                        len(self.synced_dict["OpenSignals"]["Timestamps"]),
                        len(self.synced_dict["openvibeSignal"]["Timestamps"]),
                    )
                    self.isFirstBuffer = False
                else:
                    max_size = self.getBufferMaxSize(stream_name)
                    self.checkBufferSize(
                        data,
                        max_size,
                        stream_name,
                    )
            else:
                self.slidingWindow(stream_name)
                self.fillData(data, stream_name)

    def run(self):

        streams_receiver = self.getStreams()
        self.getStreamsInfo(streams_receiver)

        active = multiprocessing.active_children()
        for child in active:
            print(child.name)

        first_timestamp = 0

        for stream in self.streams_info:
            self.synced_dict[stream["Name"]] = self.createDict(stream)
            self.info_dict[stream["Name"]] = stream
            self.info_dict[stream["Name"]]["Number full arrays"] = 0
            self.info_dict[stream["Name"]]["All arrays full"] = False

        start_time = time.perf_counter()
        elapsed_time = 0

        while elapsed_time < 20:
            print(elapsed_time)
            elapsed_time = time.perf_counter() - start_time

            if not self.isSync:
                self.syncStreams(first_timestamp)

            stream_name, data = streams_receiver.data_queue.get()

            self.getBuffers(data, stream_name)

        print(
            len(self.synced_dict["OpenSignals"]["Timestamps"]),
            len(self.synced_dict["OpenSignals"]["nSeq"]),
            len(self.synced_dict["OpenSignals"]["ECGBIT0"]),
        )

        plt.plot(self.synced_dict["OpenSignals"]["ECGBIT0"])
        plt.show()

        streams_receiver.stopChildProcesses()
        streams_receiver.terminate()
        streams_receiver.join()


if __name__ == "__main__":
    sync = Sync(buffer_window=20)
    sync.start()
    sync.join()
