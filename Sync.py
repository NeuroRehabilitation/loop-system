import time

import numpy as np

from ReceiveStreams import *


class Sync(multiprocessing.Process):
    def __init__(self, buffer_window: int):
        super().__init__()
        self.data_queue = multiprocessing.Queue()
        self.streams_info = []
        self.synced_dict, self.info_dict, self.timestamps = {}, {}, {}
        self.isSync, self.fullBuffers = False, False
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

    def checkBufferSize(self, max_size: int, stream_name: str):
        if not self.fullBuffers:
            if self.info_dict[stream_name]["Buffers Full"] == len(
                self.synced_dict[stream_name].keys()
            ):
                self.n_full_buffers += 1
                print(self.n_full_buffers)
            else:
                for key in self.synced_dict[stream_name].keys():
                    if len(self.synced_dict[stream_name][key]) == max_size:
                        self.info_dict[stream_name]["Buffers Full"] += 1

    def checkAllBuffers(self):
        if not self.fullBuffers and self.n_full_buffers == len(self.synced_dict.keys()):
            self.fullBuffers = True
            print("All buffers are full")

    def syncStreams(self, first_timestamp: int) -> None:
        if first_timestamp == 0 and len(self.timestamps.values()) > 1:
            first_timestamp = min(self.timestamps.values())
        if first_timestamp != 0:
            if all(i >= first_timestamp for i in self.timestamps.values()):
                self.isSync = True
                print("Is synced.")
                print(
                    "Timestamp OpenSignals =" + str(self.timestamps["OpenSignals"]),
                    "Timestamp Openvibe = " + str(self.timestamps["openvibeSignal"]),
                )

    def getBuffers(self, data: tuple, stream_name: str):
        if self.isSync and not self.fullBuffers:
            max_size = self.getBufferMaxSize(stream_name)
            self.checkBufferSize(
                max_size,
                stream_name,
            )
            self.fillData(data, stream_name)
        else:
            self.timestamps[stream_name] = data[1]

    def run(self):

        streams_receiver = self.getStreams()
        self.getStreamsInfo(streams_receiver)

        first_timestamp = 0

        for stream in self.streams_info:
            self.synced_dict[stream["Name"]] = self.createDict(stream)
            self.info_dict[stream["Name"]] = stream
            self.info_dict[stream["Name"]]["Buffers Full"] = 0

        start_time = time.perf_counter()
        elapsed_time = 0

        while elapsed_time < 10:
            elapsed_time = time.perf_counter() - start_time
            # print(elapsed_time)
            stream_name, data = streams_receiver.data_queue.get()
            self.checkAllBuffers()
            if not self.isSync:
                self.syncStreams(first_timestamp)
            if stream_name == "OpenSignals":
                self.getBuffers(data, stream_name)
            if stream_name == "openvibeSignal":
                self.getBuffers(data, stream_name)

        print(
            len(self.synced_dict["OpenSignals"]["Timestamps"]),
            len(self.synced_dict["OpenSignals"]["nSeq"]),
            len(self.synced_dict["OpenSignals"]["RESPBIT0"]),
            len(self.synced_dict["OpenSignals"]["EDABITREV1"]),
            len(self.synced_dict["openvibeSignal"]["Timestamps"]),
            len(self.synced_dict["openvibeSignal"]["Time(s)"]),
        )


if __name__ == "__main__":
    sync = Sync(buffer_window=5)
    sync.start()
    sync.join()
