from ReceiveStreams import *

class Sync(multiprocessing.Process):

    def __init__(self):
        super().__init__()
        self.data_queue = multiprocessing.Queue()
        self.number_processes_queue = multiprocessing.Queue()
        self.isRunning = False


    def run(self):

        streams_receiver = ReceiveStreams()
        streams_receiver.start()
        self.isRunning = True
        while self.isRunning:
            print(streams_receiver.sender_queue.get())

if __name__ == "__main__":
    sync = Sync()
    sync.start()
    sync.join()