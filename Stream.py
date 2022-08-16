import logging

from pylsl import *
import multiprocessing
import numpy as np
import time


class Streams(multiprocessing.Process):
    def __init__(self, name: str, data_queue):
        super().__init__()
        self.name = name
        self.data_queue = data_queue

    def getInlet(self):

        stream = resolve_stream("name", self.name)

        if len(stream) > 0:
            inlet = StreamInlet(stream[0], processing_flags=proc_ALL)

            return inlet

    def getType(self, inlet) -> str:
        return inlet.info().type()

    def getChannelCount(self, inlet) -> int:
        return int(inlet.info().channel_count())

    def getNominalSRate(self, inlet) -> int:
        return int(inlet.info().nominal_srate())

    def getInletInfo(self, inlet) -> dict:
        inlet_info = {
            "Name": self.name,
            "Type": self.getType(inlet),
            "Channels": self.getChannelCount(inlet),
            "Sampling Rate": self.getNominalSRate(inlet),
        }

        return inlet_info

    def run(self):

        inlet = self.getInlet()
        inlet_info = self.getInletInfo(inlet)

        while True:
            samples, timestamps = inlet.pull_sample()
            data = [samples, timestamps]
            if len(data) > 0:
                self.data_queue.put((inlet_info["Name"],data))
