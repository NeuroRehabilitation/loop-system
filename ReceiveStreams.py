import multiprocessing

from Stream import *
import sys, signal


class ReceiveStreams(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        (
            self.stream_names,
            self.streams_inlet,
            self.streams_info,
        ) = ([], [], [])
        self.data_queue = multiprocessing.Queue()
        self.info_queue = multiprocessing.Queue()

    def availableStreams(self) -> list:

        streams = resolve_streams()

        for stream in streams:
            self.stream_names.append(stream.name())

        return self.stream_names

    def startProcess(self, name):

        stream = Streams(name, self.data_queue)
        inlet = stream.getInlet()
        inlet_info = stream.getInletInfo(inlet)
        stream.start()
        print(f"Process Started {stream.name}")

        return stream, inlet_info

    def stopChildProcesses(self):
        # get all active child processes
        active = multiprocessing.active_children()
        # terminate all active children
        for child in active:
            child.terminate()
        for child in active:
            child.join()

    def run(self) -> None:

        self.stream_names = self.availableStreams()

        for name in self.stream_names:
            stream, inlet_info = self.startProcess(name)
            self.streams_info.append(inlet_info)
        self.info_queue.put(self.streams_info)
