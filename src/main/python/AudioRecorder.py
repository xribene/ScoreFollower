from PyQt5.QtCore import (QObject, pyqtSignal, pyqtSlot, QMutex)
import pyaudio
import queue
import wave
import numpy as np
import logging
from collections import deque
#%%
#%%
class AudioRecorder(QObject):
    '''
    AudioRecorder(QObject): thread which accepts input from specified
    audio input device (default is 0) in chunks, then pushes audio to
    queue for processing by Chromatizer thread.
    '''
    signalToChromatizer = pyqtSignal(object)
    # signalEnd = pyqtSignal()
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
        # self.deque = deque(rate*1)
        self.p = pyaudio.PyAudio()
        self.input_device_index = input_device_index

        self.createStream()
        self.stopped = True
        self.frames = []

        logging.warning("audio recorder init done")


    def createStream(self):
        if self.file == None:
            self.stream = self.p.open(format= pyaudio.paInt16,
                                    start = False,
                                    channels = 1,
                                    rate = self.rate,
                                    input = True,
                                    # output = True,
                                    # input_device_index = self.input_device_index,
                                    frames_per_buffer = self.chunk,
                                    stream_callback = self._callback)
        else:
            self.stream = self.p.open(
                                    format=self.p.get_format_from_width(self.file.getsampwidth()),
                                    channels = self.file.getnchannels(),
                                    start = False,
                                    rate = self.rate,
                                    input = True,
                                    output = True,
                                    frames_per_buffer = self.chunk,
                                    stream_callback = self._callback)
        
    def reset(self):
        self.stopStream()
        if self.file is not None:
            self.file.setpos(0)
    def startStopStream(self):
        if self.stopped:
            self.startStream()
        else:
            self.stopStream()

    def startStream(self):
        if self.stopped:
            self.stream.start_stream()
            self.stopped = False

    def stopStream(self):
        if not self.stopped:
            self.stream.stop_stream()
            self.stopped = True

    def closeStream(self):
        self.stream.stop_stream()
        self.stream.close()

        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = self.rate
        WAVE_OUTPUT_FILENAME = "record.wav"
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        self.p.terminate()
        if self.file:
            self.file.close()

    def  _callback(self, in_data, frame_count, time_info, status):
        """
        grab data from buffer,
        put data and rate into queue
        continue
        """
        # logging.debug(f"in callback {frame_count}")

        if self.file != None:
            data = self.file.readframes(frame_count)
            data = np.frombuffer(data, "int16")
            data_per_channel=[data[chan::self.file.getnchannels()] for chan in range(self.file.getnchannels())]
        
            # mono = (data_per_channel[0] + data_per_channel[1])/2
            mono = data_per_channel[0]
            self.signalToChromatizer.emit(mono)
            # self.queue.push(mono)
            self.i += 1
            # print(self.i)
            self.frames.append(data)
        else:
            data = np.frombuffer(in_data, "int16")
            self.signalToChromatizer.emit(data)
            # self.queue.push(data)
            self.frames.append(in_data)
        return (data, pyaudio.paContinue)


if __name__ == "__main__":
    import queue
    from pathlib import Path
    import time
    readQueue = queue.Queue()
    audioRecorder = AudioRecorder(queue = readQueue, 
                                        # wavfile =  "/home/xribene/Projects/ScoreFollower/src/main/python/offline/jeteeFF.wav", # None,#
                                        rate = 44100,
                                        # ! be careful, audio streams chunk is 
                                        # ! equal to the hop_length
                                        chunk = 1024,
                                        input_device_index=12)
    
    audioRecorder.startStopStream()
    time.sleep(1000)
    # print(audioRecorder.i)