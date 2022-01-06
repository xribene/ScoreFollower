from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot)
import pyaudio
import queue
import wave
import numpy as np
import logging
class AudioRecorder(QObject):
    '''
    AudioRecorder(QObject): thread which accepts input from specified
    audio input device (default is 0) in chunks, then pushes audio to
    queue for processing by Chromatizer thread.
    '''
    signalToChromatizer = pyqtSignal(object)
    signalEnd = pyqtSignal()
    def __init__(self, queue, wavfile=None, rate = 22050, chunk = 4096,
                       input_device_index = 0):
        QObject.__init__(self)
        self.rate = rate
        self.i=0

        if wavfile != None:
            self.file = wave.open(wavfile, 'r')
        else:
            self.file = None
        self.chunk = chunk
        self.queue = queue
        self.p = pyaudio.PyAudio()
        self.input_device_index = input_device_index

        self.createStream()
        logging.warning("audio recorder init done")


    def createStream(self):
        if self.file == None:
            self.stream = self.p.open(format= pyaudio.paFloat32,
                                    channels = 1,
                                    rate = self.rate,
                                    input = True,
                                    # output = True,
                                    # input_device_index = self.input_device_index,
                                    frames_per_buffer = self.chunk,
                                    stream_callback = self._callback)
        else:
            self.stream = self.p.open(format=self.p.get_format_from_width(self.file.getsampwidth()),
                                    channels = self.file.getnchannels(),
                                    rate = self.rate,
                                    input = True,
                                    output = True,
                                    frames_per_buffer = self.chunk,
                                    stream_callback = self._callback)
        self.stop = False

        # ? Is this important ? Seems to work fine without it
        self.startStream()

    def startStream(self):
        self.stream.start_stream()

    def stopStream(self):
        self.stream.stop_stream()

    def closeStream(self):
        self.stream.close()
        self.p.terminate()
        self.file.close()

    def  _callback(self, in_data, frame_count, time_info, status):
        """
        grab data from buffer,
        put data and rate into queue
        continue
        """
        logging.debug(f"in callback {frame_count}")

        if self.file != None:
            data = self.file.readframes(frame_count)
            if self.i < 3800:
                data = np.frombuffer(data, "int16")
                data_per_channel=[data[chan::self.file.getnchannels()] for chan in range(self.file.getnchannels())]
                mono = (data_per_channel[0] + data_per_channel[1])/2
                self.signalToChromatizer.emit(mono)
                self.i += 1
            else:
                self.signalEnd.emit()
                return (data, pyaudio.paAbort)
            # else:
            #     logging.debug("stopping stream")
            #     # self.stopStream()
            #     self.signalEnd.emit()
            # if self.i == 100:
            #     logging.debug("early stopping stream")
            #     # self.stopStream()
            #     # self.closeStream()
            #     # self.signalEnd.emit()

        else:
            data = np.frombuffer(in_data, "float32")
            self.signalToChromatizer.emit(data)
        return (data, pyaudio.paContinue)
