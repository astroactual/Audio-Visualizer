import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, QThread
import pyaudiowpatch as pyaudio
import numpy as np
import sounddevice as sd
import numpy as np
import sys

#TODO possibly reinvent the wheel with this: https://medium.com/geekculture/real-time-audio-wave-visualization-in-python-b1c5b96e2d39

# a QThread for audio data reading
class AudioDataThread(QThread):

    new_lr_data = pyqtSignal(tuple) # pyqtSignal for sending data

    thread_continue = True

    def __init__(self):
        super().__init__(None)
        self.p=pyaudio.PyAudio() #start PyAudio instance
        self.stream:pyaudio.Stream

        # TODO: make rate and channels variable based on the audio device configuration
        self.CHUNK = 2**11       #num of data points read at one time
        self.RATE = 48000        #time resolution of the recording device (Hz)
        self.CHANNELS = 2        #stereo usually has 2 channels
        self.maxValue = 2**15
        self.bars = 50

        default_output = sd.query_devices(kind='output')    #find default audio device
        print(f"Default: {default_output['name']}")

        #for all devices connected, compare names. If default device name has the word "Loopback", set as PyAudio device index
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            print ( i, dev.get('name'))
            if default_output['name'] in dev.get('name') and "[Loopback]" in dev.get('name'):
                print (f"This is default device from array {dev.get('name')} at index {i}")
                dev_index = i   #assign dev index to current index

        self.stream = self.p.open(format=pyaudio.paInt16,channels=self.CHANNELS, rate=self.RATE, input=True, input_device_index=dev_index, frames_per_buffer=self.CHUNK)

    # get the left and right data
    def get_lr_data(self):
        data = np.frombuffer(self.stream.read(1024),dtype=np.int16)
        dataL = data[0::2]
        dataR = data[1::2]
        return dataL, dataR

    # close audio stream and terminate pyaudio
    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def kill(self): # lol
        self.thread_continue = False

    # the QThread loop function
    def run(self):
        # loop until thread_continue is set to False
        while self.thread_continue:
            dataL, dataR = self.get_lr_data()
            self.new_lr_data.emit((dataL, dataR)) # emit the data as a QT Signal to be captured in a QT Slot
        
        # close that ish
        self.close()

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.central = QWidget()
        self.central_layout = QVBoxLayout()
        self.central.setLayout(self.central_layout)

        self.peak_visualizer = pg.plot()
        self.peak_visualizer.setInteractive(False)
        self.central_layout.addWidget(self.peak_visualizer)

        self.spec_visualizer = pg.plot()
        # self.spec_visualizer.setInteractive(False)
        self.central_layout.addWidget(self.spec_visualizer)

        self.setCentralWidget(self.central)

        # setting window title to plot window
        self.setWindowTitle("Audio Visualization")
        
        # how long the graph is
        self.num_samples = 25

        # create list for each audio channel
        self.left_peak_audio_levels = [0] * self.num_samples
        self.right_peak_audio_levels = [0] * self.num_samples

        # create horizontal list i.e x-axis
        self.peak_x = [i for i in range(self.num_samples)]

        self.num_spec_bytes = 513

        self.left_spec_audio_levels = np.array([0] * self.num_spec_bytes)
        self.right_spec_audio_levels = np.array([0] * self.num_spec_bytes)

        # create horizontal list i.e x-axis
        self.spec_x = [i for i in range(self.num_spec_bytes)]

        # create pyqt5graph bar graph item
        # with width = 0.6
        # with bar colors = green
        self.left_peak_graph = pg.BarGraphItem(x = self.peak_x, height = self.left_peak_audio_levels, width = .6, brush ='g')
        self.right_peak_graph = pg.BarGraphItem(x = self.peak_x, height = self.right_peak_audio_levels, width = .6, brush ='g')

        self.left_spec_graph = pg.BarGraphItem(x = self.spec_x, height = self.left_spec_audio_levels, width = 40, brush ='w')
        self.right_spec_graph = pg.BarGraphItem(x = self.spec_x, height = self.right_spec_audio_levels, width = 40, brush ='w')

        # add item to plot window
        # adding bargraph item to the window
        self.peak_visualizer.addItem(self.left_peak_graph)
        self.peak_visualizer.addItem(self.right_peak_graph)
        self.peak_visualizer.setYRange(-0.5, 0.5)

        self.spec_visualizer.addItem(self.left_spec_graph)
        self.spec_visualizer.addItem(self.right_spec_graph)
        self.spec_visualizer.setXRange(0, 5000)
        self.spec_visualizer.setYRange(-900000, 900000)

        # create the audio data reading thread
        self.audio_data_thread = AudioDataThread()
        # connect the data signal to the update function
        self.audio_data_thread.new_lr_data.connect(self.update_visualizer)
        # start the thread
        self.audio_data_thread.start()

    #code below is for terminal visualization (for testing)
    def terminal_visualization(self, dataL, dataR):
        peakL = np.abs(np.max(dataL)-np.min(dataL))/self.audio_data_thread.maxValue
        peakR = -1 * np.abs(np.max(dataR)-np.min(dataR))/self.audio_data_thread.maxValue
        lString = "#"*int(peakL*self.audio_data_thread.bars)+"-"*int(self.audio_data_thread.bars-peakL*self.audio_data_thread.bars)
        rString = "#"*int(peakR*self.audio_data_thread.bars)+"-"*int(self.audio_data_thread.bars-peakR*self.audio_data_thread.bars)
        print("L=[%s]\tR=[%s]"%(lString, rString))

    def update_visualizer(self, lrdata):
        dataL, dataR = lrdata
        peakL = np.abs(np.max(dataL)-np.min(dataL))/self.audio_data_thread.maxValue
        peakR = -1 * np.abs(np.max(dataR)-np.min(dataR))/self.audio_data_thread.maxValue
        
        # there has to be a better way to do what is about to be coded

        # remove the first item from the list (left most sample)
        self.left_peak_audio_levels.pop(0)
        self.right_peak_audio_levels.pop(0)
        # remove THE ENTIRE  left and right graphs (super inefficient)
        self.peak_visualizer.removeItem(self.left_peak_graph)
        self.peak_visualizer.removeItem(self.right_peak_graph)
        # append the newest value to the audio levels array
        self.left_peak_audio_levels.append(peakL)
        self.right_peak_audio_levels.append(peakR)
        # COMPLETLEY RECREATE THE left and right graphs (continuing inefficency)
        self.left_peak_graph = pg.BarGraphItem(x = self.peak_x, height = self.left_peak_audio_levels, width = 0.6, brush ='g')
        self.right_peak_graph = pg.BarGraphItem(x = self.peak_x, height = self.right_peak_audio_levels, width = 0.6, brush ='g')
        # and the newly created graphs back to the visualizer
        self.peak_visualizer.addItem(self.left_peak_graph)
        self.peak_visualizer.addItem(self.right_peak_graph)

        self.spec_visualizer.removeItem(self.left_spec_graph)
        self.spec_visualizer.removeItem(self.right_spec_graph)

        # alpha filter smoothing formula: smoothed = (new_data * alpha) + (last_smoothed * beta)
        #                                   where last_smoothed = the smoothed value from the previous new_data collection
        #                                   alpha is a float percent (0.0 through 1.0)
        #                                   beta = 1 - alpha
        # parameters for alpha filter
        alpha = 0.5 # or a 50% weight with the last sample
        beta = 1 - alpha

        # spectrogram is tough and requires FAST FORIER TRANSFORMS which is diffeq stuff so we'll let numpy handle the specifics
        # learned what i needed from this https://www.yhoka.com/en/posts/fft-python/
        self.spec_visualizer.removeItem(self.left_spec_graph)
        self.spec_visualizer.removeItem(self.right_spec_graph)

        dataL_y = np.abs(np.fft.rfftn(dataL).astype(np.float64))
        dataL_x = np.fft.rfftfreq(len(dataL), 1 / self.audio_data_thread.RATE)
        self.left_spec_audio_levels = (dataL_y * alpha) + (self.left_spec_audio_levels * beta) # applying alpha filter
        self.left_spec_graph = pg.BarGraphItem(x = dataL_x, height = self.left_spec_audio_levels, width = 45, brush ='w')

        dataR_y = -1 * np.abs(np.fft.rfftn(dataR).astype(np.float64))
        dataR_x = np.fft.rfftfreq(len(dataR), 1 / self.audio_data_thread.RATE)
        self.right_spec_audio_levels = (dataR_y * alpha) + (self.right_spec_audio_levels * beta) # applying alpha filter
        self.right_spec_graph = pg.BarGraphItem(x = dataR_x, height = self.right_spec_audio_levels, width = 45, brush ='w')

        self.spec_visualizer.addItem(self.left_spec_graph)
        self.spec_visualizer.addItem(self.right_spec_graph)
        # i know theres a simpler data update but im lazy and this works

# main method
if __name__ == "__main__":
    app = QApplication(sys.argv) # pass args to the app class
    AudioVisualizer = MainWindow() # create the visualizer main window object
    AudioVisualizer.show() # show that bish on the screen
    app.exec() # start the qt even loop

