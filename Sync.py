from ReceiveStreams import *


class Sync(multiprocessing.Process):
    def __init__(self, buffer_window: int):
        super().__init__()
        self.data_queue, self.buffer_queue = (
            multiprocessing.Queue(),
            multiprocessing.Queue(),
        )
        self.streams_info = []
        self.synced_dict, self.info_dict, self.timestamps = {}, {}, {}
        self.isSync, self.isFirstBuffer = False, True
        self.startAcquisition = multiprocessing.Value("i", 0)
        self.n_full_buffers = 0
        self.buffer_window = buffer_window

    def getStreams(self):
        """Function to instantiate class ReceiveStreams"""
        streams_receiver = ReceiveStreams()
        streams_receiver.start()

        return streams_receiver

    def getStreamsInfo(self, streams_receiver) -> None:
        """Get streams information"""
        self.streams_info = streams_receiver.info_queue.get()

    def createDict(self, stream_info: dict) -> dict:
        """Create dictionary with data from each stream

        keys of the dictionary are the channels of the stream - columns labels

        """
        columns_labels = ["Timestamps"]
        for key in stream_info["Channels Info"].keys():
            columns_labels.append(stream_info["Channels Info"][key][0])
        dict = {key: [] for key in columns_labels}

        return dict

    def fillData(self, data: tuple, stream_name: str) -> None:
        """Fill the dictionary of each stream with the data from the stream"""
        self.synced_dict[stream_name]["Timestamps"].append(data[1])
        for i, key in enumerate(self.synced_dict[stream_name].keys()):
            if key != "Timestamps":
                self.synced_dict[stream_name][key].append(data[0][i - 1])

    def getBufferMaxSize(self, stream_name: str) -> int:
        """Set the size of the buffer to send to process - window*fs"""
        return int(self.buffer_window * self.info_dict[stream_name]["Sampling Rate"])

    def checkBufferSize(self, data: tuple, max_size: int, stream_name: str):
        """Check if all the buffers are full before sending to process"""
        if self.isSync:
            if self.info_dict[stream_name]["Number full arrays"] == len(
                self.synced_dict[stream_name].keys()
            ):
                self.n_full_buffers += 1
            else:
                for key in self.synced_dict[stream_name].keys():
                    if len(self.synced_dict[stream_name][key]) == max_size:
                        self.info_dict[stream_name]["Number full arrays"] += 1

    def slidingWindow(self, stream_name: str):
        print("Sliding Window")
        """Create Sliding window to update the oldest element of the array (index 0) with the newest sample"""
        for key in self.synced_dict[stream_name].keys():
            self.synced_dict[stream_name][key].pop(0)

    def syncStreams(self, first_timestamp: int) -> None:
        """Synchronize streams by comparing the first timestamp of each stream"""

        if first_timestamp == 0 and len(self.timestamps.values()) > 0:
            first_timestamp = min(self.timestamps.values())
        if first_timestamp != 0:
            if all(i >= first_timestamp for i in self.timestamps.values()):
                self.isSync = True
                print("Streams are Synced.")
                print(first_timestamp)

    def getBuffers(self, data: tuple, stream_name: str):
        """Function to get the buffers already synced"""
        if not self.isSync:
            self.timestamps[stream_name] = data[1]
        else:
            if self.isFirstBuffer:
                self.fillData(data, stream_name)
                if self.n_full_buffers == len(self.synced_dict.keys()):
                    self.isFirstBuffer = False
                else:
                    self.checkBufferSize(
                        data,
                        self.info_dict[stream_name]["Max Size"],
                        stream_name,
                    )
            else:
                self.slidingWindow(stream_name)
                self.fillData(data, stream_name)
                self.buffer_queue.put(self.synced_dict)

    def run(self):

        streams_receiver = self.getStreams()
        self.getStreamsInfo(streams_receiver)
        first_timestamp = 0

        for stream in self.streams_info:
            self.synced_dict[stream["Name"]] = self.createDict(stream)
            self.info_dict[stream["Name"]] = stream
            self.info_dict[stream["Name"]]["Max Size"] = self.getBufferMaxSize(
                stream["Name"]
            )
            self.info_dict[stream["Name"]]["Number full arrays"] = 0

        while bool(self.startAcquisition.value):
            if not self.isSync:
                stream_name, data_temp = streams_receiver.data_queue.get()
                self.getBuffers(data_temp, stream_name)
                self.syncStreams(first_timestamp)
            else:
                stream_name, data = streams_receiver.data_queue.get()
                self.getBuffers(data, stream_name)

        streams_receiver.stopChildProcesses()
        streams_receiver.terminate()
        streams_receiver.join()
