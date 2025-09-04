# 🪢 Loop System

## About

This application is designed to retrieve [Lab Streaming Layer](https://github.com/sccn/labstreaminglayer) streams
containing physiological data, synchronize and process the signals to obtain features in real-time.

The system uses parallel processing, therefore each class is a Process in Python.

## The following chart shows how the system works:

```mermaid
flowchart LR
    %% =============================
    %% Nodes
    %% =============================

    Stream(["**Stream**<br/>(multiprocessing.Process)<br/><br/>Class that initializes all available LSL streams<br/>Pulls samples from each available stream and puts the data in a Queue."])
    Receive(["**Receive Streams**<br/>(multiprocessing.Process)<br/><br/>Instantiates Stream objects for each available stream<br/>Starts each stream process, gets data and info from Queue, and sends to next process."])
    Sync(["**Sync**<br/>(multiprocessing.Process)<br/><br/>Synchronizes data using timestamps<br/>Organizes into dictionaries for each LSL stream.<br/><br/>**Buffer Data**<br/>Continuously updates buffer, sends to Manager when full.<br/><br/>**Data to Train**<br/>When self-report is submitted, sends training data to Queue."])
    Manager(["**Manager**<br/>(multiprocessing.Process)<br/><br/>Controls flow between processes.<br/>Receives buffer and training data from Sync.<br/>Extracts features, predicts stress level.<br/>Sends training data to Model Trainer.<br/>Updates model after retraining.<br/>Sends predictions to FOF using LSL."])
    Processing(["**Processing**<br/><br/>Static class with functions to process and obtain features.<br/>Predicts stress level from model."])
    Trainer(["**Model Trainer**<br/>(multiprocessing.Process)<br/><br/>Performs online retraining of models.<br/>If true label differs from prediction, retrains model and updates Manager."])
    Output(["**Stress Prediction**<br/>(Low, Medium, High)<br/>Prediction Probability<br/>Model Version"])

    %% =============================
    %% Connections
    %% =============================

    Stream -->|"Data Queue"| Receive
    Receive -->|"Data Queue<br/>Info Queue"| Sync
    Sync -->|"Buffer Data Queue<br/>Data Train Queue"| Manager
    Sync -.->|"🔒 Sync Lock"| Manager
    Manager -->|"Features from Buffer Data<br/>Features from Training Data"| Processing
    Manager -->|"Train Lock 🔒"| Trainer
    Trainer -->|"Model Trainer Lock 🔒"| Manager
    Manager --> Output

    %% =============================
    %% Styling
    %% =============================

    classDef process fill:#f2f2f2,stroke:#333,stroke-width:1px,color:#000,rx:10,ry:10
    classDef output fill:#b3e6b3,stroke:#333,stroke-width:1px,color:#000,rx:50,ry:50

    class Stream,Receive,Sync,Manager,Processing,Trainer process
    class Output output
```

## Here are a brief explanation of the functionality of each class:

- `Stream` is a class that initializes all available LSL streams. The `run()` method of this class is responsible for
  pulling the samples
  from each stream, and adding them to a Queue.

- `ReceiveStreams` is a class that instantiates `Stream` objects for each available stream, and starts their processes.
  It also gets the stream information and puts it in a Queue.

- `Sync` is a class that retrieves data from the Queue of the class ReceiveStreams, and synchronizes the data by
  timestamps. It also organizes the data in a dictionary with keys matching the LSL Streams. Finally, it puts and
  continuously updates the data in a buffer
  queue with 40 sec of data and sends this data to the manager to process the features.

- `Processing` is a class of static methods that receives data from the buffer queue, and processes it to extract
  features. The extracted
  features are then returned in the Manager process.

- `Signals_Processing` is a class that contains all the static methods to process the physiological features.

- `Training Model` is a class that processes the physiological data and obtains the machine learning models during the
  training phase (calibration) of the system, to be used in real-time.

- `Manager` is a class that instantiates `Sync` and `Processing` objects, and starts the `Sync` process. It also sets a
  flag to start data acquisition. The `run()` method in this class retrieves data from the buffer queue (when there is a
  buffer available) and sends it for processing. Once there is a buffer being processed, the queue of buffers remains
  empty (the buffer is
  continuously updated in the `Sync` process) until it returns a prediction. This process is performed in a loop.

```mermaid
sequenceDiagram
ReceiveStreams ->> Sync: getStreamsInfo()
Sync ->> ReceiveStreams: info_queue.get()
Sync ->> Manager: info_queue.put()
Sync ->> ReceiveStreams: data_queue.get()
ReceiveStreams ->> Sync: data_queue.put()
Sync ->> Manager: buffer_queue.put()
Manager ->> Sync: startAcquisition.value = 1
Manager ->> Sync: startAcquisition.value = 0
Manager ->> Process: data = buffer_queue.get()
Process ->> Manager: features = processData()
```
