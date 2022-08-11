from Stream import *


class ReceiveStreams(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        (
            self.stream_processes,
            self.stream_names,
            self.streams_inlet,
            self.streams_info,
        ) = ([], [], [], [])
        self.n_processes = 0
        self.receiver_queue = multiprocessing.Queue()
        self.sender_queue = multiprocessing.Queue()

    def availableStreams(self) -> list:

        streams = resolve_streams()

        for stream in streams:
            self.stream_names.append(stream.name())

        return self.stream_names

    def startProcess(self, name):

        stream = Streams(name)
        inlet = stream.getInlet()
        inlet_info = stream.getInletInfo(inlet)
        print(inlet_info)
        stream.start()
        print(f"Process Started {stream.name}")

        return stream, inlet, inlet_info

    def acquireData(self, process) -> None:
        while not process.data_queue.empty():
            self.receiver_queue.put(process.data_queue.get())

    def stopProcess(self, process) -> None:
        process.join()
        print("Process {} finished.".format(process.name))
        self.n_processes -= 1

    def run(self) -> None:

        self.stream_names = self.availableStreams()

        for name in self.stream_names:
            stream, inlet, inlet_info = self.startProcess(name)
            self.streams_inlet.append(inlet)
            self.streams_info.append(inlet_info)
            self.stream_processes.append(stream)
            self.n_processes += 1

        print("Started all streams.")

        while self.n_processes > 0:
            for process in self.stream_processes:
                # print("Process {}".format(process.name))
                self.acquireData(process)
                if not self.receiver_queue.empty():
                    data = self.receiver_queue.get()
                    samples, timestamps = data
                    data_chunk = [samples, timestamps]
                    if len(data_chunk[0]) > 0 and len(data_chunk[1]) > 0:
                        self.sender_queue.put(data_chunk)
                        # print(self.sender_queue.qsize())


# if __name__ == "__main__":
#     receiver = ReceiveStreams()
#     receiver.startProcess("OpenSignals")
