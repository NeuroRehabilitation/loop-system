import time

import numpy as np

from ReceiveStreams import *


class Sync(multiprocessing.Process):
    def __init__(self, buffer_window: int):
        super().__init__()
        self.data_queue = multiprocessing.Queue()
        self.streams_info = []
        self.synced_dict = {}
        self.isSync = False
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

    def run(self):

        streams_receiver = self.getStreams()
        self.getStreamsInfo(streams_receiver)

        for stream in self.streams_info:
            self.synced_dict[stream["Name"]] = self.createDict(stream)

        start_time = time.perf_counter()
        elapsed_time = 0
        first_timestamp, timestamp_opensignals, timestamp_openvibe = 0, 0, 0

        while elapsed_time < 20:
            elapsed_time = time.perf_counter() - start_time
            # print(elapsed_time)
            stream_name, data = streams_receiver.data_queue.get()
            if stream_name == "OpenSignals":
                if self.isSync:
                    self.fillData(data, stream_name)
                else:
                    timestamp_opensignals = data[1]
            if stream_name == "openvibeSignal":
                if self.isSync:
                    self.fillData(data, stream_name)
                else:
                    timestamp_openvibe = data[1]
            if not self.isSync:
                if first_timestamp == 0:
                    first_timestamp = np.min(timestamp_openvibe, timestamp_opensignals)
                else:
                    if (
                        timestamp_opensignals >= first_timestamp
                        and timestamp_openvibe >= first_timestamp
                    ):
                        self.isSync = True
                        print("Is synced.")
                        print(f"Time elapsed = {elapsed_time}")
                        print(
                            f"Timestamp OpenSignals = {timestamp_opensignals}",
                            f"Timestamp Openvibe = {timestamp_openvibe}",
                        )

        print(
            len(self.synced_dict["OpenSignals"]["Timestamps"]),
            len(self.synced_dict["OpenSignals"]["nSeq"]),
            len(self.synced_dict["OpenSignals"]["RESPBIT0"]),
            len(self.synced_dict["OpenSignals"]["EDABITREV1"]),
            len(self.synced_dict["openvibeSignal"]["Timestamps"]),
            len(self.synced_dict["openvibeSignal"]["Time(s)"]),
        )


if __name__ == "__main__":
    sync = Sync(buffer_window=40)
    sync.start()
    sync.join()
