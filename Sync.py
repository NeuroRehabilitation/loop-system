import multiprocessing

from ReceiveStreams import *

# from Plot import *
import time
import random

# import main


class Sync(multiprocessing.Process):
    def __init__(self, buffer_window: int) -> None:
        """
        :param buffer_window: time of the window to fill with buffers of data in seconds;
        :type buffer_window: int
        """

        super().__init__()

        # info_queue - Queue with the information of the streams
        # buffer_queue - Queue with each buffer of data to send to Manager.py
        # data_queue - Queue with the data of the streams from ReceiveStreams.py
        (
            self.data_queue,
            self.buffer_queue,
            self.markers_queue,
            self.valence_queue,
            self.arousal_queue,
            self.info_queue,
        ) = (
            multiprocessing.Queue(),
            multiprocessing.Queue(),
            multiprocessing.Queue(),
            multiprocessing.Queue(),
            multiprocessing.Queue(),
            multiprocessing.Queue(),
        )

        # List with the stream info
        self.streams_info = []

        # Dictionaries to organize the data of all the streams
        self.synced_dict, self.info_dict, self.timestamps = {}, {}, {}

        # Flag to check if buffers are synced, if it is the first buffer of data
        self.isSync, self.isFirstBuffer = False, True

        # Flag to start the acquisition of data by the Manager.
        self.startAcquisition = multiprocessing.Value("i", 0)
        self.startBuffer = multiprocessing.Value("i", 0)

        # Number of full buffers from all the streams
        self.n_full_buffers = 0

        # Buffer window in seconds
        self.buffer_window = buffer_window

    def getStreams(self):
        """
        Function to instantiate class ReceiveStreams and start the process ReceiveStreams;

        :return: returns object of class ReceiveStreams();

        """
        streams_receiver = ReceiveStreams()
        streams_receiver.start()

        return streams_receiver

    def getStreamsInfo(self, streams_receiver) -> None:
        """
        Function to get information about the streams and pass that information to a Queue

        :param streams_receiver: object of class ReceiveStreams()

        """

        self.streams_info = streams_receiver.info_queue.get()
        self.info_queue.put(self.streams_info)

    def createDict(self, stream_info: dict) -> dict:
        """
        Function to create dictionary for each stream with the channels names. columns_labels are the channels names.

        :param stream_info: dictionary with information about the stream
        :type stream_info: dict
        :return: dictionary with all the channels from the stream
        :rtype: dict
        """
        columns_labels = ["Timestamps"]
        for key in stream_info["Channels Info"].keys():
            columns_labels.append(stream_info["Channels Info"][key][0])
        dict = {key: [] for key in columns_labels}

        return dict

    def fillData(self, data: tuple, stream_name: str) -> None:
        """Function to fill the dictionary synced_dict with the data from each stream

        :param data: data from the streams
        :type data: tuple -[(nseq,value),timestamp]
        :param stream_name: name of the stream
        :type stream_name: str
        """

        self.synced_dict[stream_name]["Timestamps"].append(data[1])
        for i, key in enumerate(self.synced_dict[stream_name].keys()):
            if key != "Timestamps":
                self.synced_dict[stream_name][key].append(data[0][i - 1])

    def getBufferMaxSize(self, stream_name: str) -> int:
        """Set the maximum size of the buffer to fill with data

        :param stream_name: name of the stream
        :type stream_name: str
        :return: max buffer size - window*fs
        :rtype: int
        """

        return int(self.buffer_window * self.info_dict[stream_name]["Sampling Rate"])

    def checkBufferSize(self, max_size: int, stream_name: str) -> None:
        """Check if buffers are synchronized and then check the size of the buffers for every stream

        :param max_size: maximum size of the buffer
        :type max_size:int
        :param stream_name: name of the stream
        :type stream_name: str
        """

        if self.isSync:
            if self.info_dict[stream_name]["Number full arrays"] == len(
                self.synced_dict[stream_name].keys()
            ):
                self.n_full_buffers += 1
            else:
                for key in self.synced_dict[stream_name].keys():
                    if len(self.synced_dict[stream_name][key]) == max_size:
                        self.info_dict[stream_name]["Number full arrays"] += 1

    def slidingWindow(self, stream_name: str) -> None:
        """Create Sliding window to remove the oldest element of the array (index 0) and add the newest sample value

        :param stream_name: name of the stream
        :type stream_name: str
        """

        for key in self.synced_dict[stream_name].keys():
            self.synced_dict[stream_name][key].pop(0)

    def syncStreams(self, first_timestamp: int) -> None:
        """Synchronize streams:
            check if the timestamps from all the streams are higher than the minimum timestamp.
            Streams are synchronized if condition is true.

        :param first_timestamp: minimum timestamp of all the streams
        :type first_timestamp: int
        """

        if first_timestamp == 0 and len(self.timestamps.values()) > 0:
            first_timestamp = min(self.timestamps.values())
        if first_timestamp != 0:
            if all(i >= first_timestamp for i in self.timestamps.values()):
                self.isSync = True
                print("Streams are Synced.")

    def getBuffers(self, data: tuple, stream_name: str) -> None:
        """

        :param data: data from the streams
        :type data: tuple
        :param stream_name: name of the streams
        :type stream_name: str

        """

        # If the data is not synchronized keep putting the timestamps from each stream on the dictionary self.timestamps
        if not self.isSync:
            self.timestamps[stream_name] = data[1]
        # In case of the data being synchronized
        else:
            if self.isFirstBuffer:  # In case it is the first buffer of data
                self.fillData(data, stream_name)
                # Fills the first buffer of data with data
                if "PsychoPy" not in stream_name:
                    if self.n_full_buffers == len(
                        self.synced_dict.keys()
                    ):  # If first buffer has reached the maximum size put flag isFirstBuffer to False
                        self.isFirstBuffer = False

                    else:
                        # If buffers are not full keep checking the size of the buffers
                        self.checkBufferSize(
                            self.info_dict[stream_name]["Max Size"],
                            stream_name,
                        )
            else:
                # If it is not the first buffer (buffers are with max size)
                # Start sliding window and put buffers on the Queue to send to process

                self.slidingWindow(stream_name)
                self.fillData(data, stream_name)
                self.buffer_queue.put(self.synced_dict)

    def getPsychoPyData(self, data: tuple, stream_name: str) -> None:
        if "Markers" in stream_name:
            self.markers_queue.put(data[0])
        else:
            if "Arousal" in data[0][0]:
                self.arousal_queue.put(data[0][1])
            else:
                self.valence_queue.put(data[0][1])

    def fill_any(self, i):
        fill_var = []
        while len(fill_var) < i:
            fill_var.append(0)
        return fill_var

    def SendData_To_Display(self, q, data):
        q.put(data)
        # print("DATA SENT : ", data, ".\n")
        time.sleep(0.01)

    def run(self):
        q = multiprocessing.Queue()
        data_stream = self.fill_any(10000)
        q.put(data_stream)

        # p2 = multiprocessing.Process(target=main.Run, args=(q,))
        # p2.start()

        # Start all the available streams
        streams_receiver = self.getStreams()

        # Get the information from the streams
        self.getStreamsInfo(streams_receiver)
        first_timestamp = 0

        # For every streams available create and fill the dictionary synced_dict with:
        # Name of the stream, Maximum Size of the buffers, Number of channels filled with data
        for stream in self.streams_info:
            self.synced_dict[stream["Name"]] = self.createDict(stream)
            self.info_dict[stream["Name"]] = stream
            self.info_dict[stream["Name"]]["Max Size"] = self.getBufferMaxSize(
                stream["Name"]
            )
            self.info_dict[stream["Name"]]["Number full arrays"] = 0

        # Loop to receive the data - start acquisition is true
        while bool(self.startAcquisition.value):
            # If data is not synced, retrieve data from the queue but don't use it
            # Synchronize the data
            if not self.isSync:
                stream_name, data_temp = streams_receiver.data_queue.get()
                self.getBuffers(data_temp, stream_name)
                self.syncStreams(first_timestamp)
                if "PsychoPy" in stream_name:
                    self.getPsychoPyData(data_temp, stream_name)
            else:
                # If data is synced, get the data from the queue and fill the buffers with data
                stream_name, data = streams_receiver.data_queue.get()
                if "PsychoPy" in stream_name:
                    self.getPsychoPyData(data, stream_name)
                else:
                    # if bool(self.startBuffer.value):
                    self.getBuffers(data, stream_name)
                    # data_stream.pop(0)
                    # data_stream.append(data[0][1])
                    # self.SendData_To_Display(q, data_stream)

        # Stop all running child processes
        streams_receiver.stopChildProcesses()
        streams_receiver.terminate()
        streams_receiver.join()
