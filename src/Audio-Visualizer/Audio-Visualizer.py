
import pyaudiowpatch as pyaudio
import numpy as np
import sounddevice as sd


#TODO possibly reinvent the wheel with this: https://medium.com/geekculture/real-time-audio-wave-visualization-in-python-b1c5b96e2d39


default_output = sd.query_devices(kind='output')    #find default audio device
print(f"Default: {default_output['name']}")


p=pyaudio.PyAudio() #start PyAudio instance


#for all devices connected, compare names. If default device name has the word "Loopback", set as PyAudio device index
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print ( i, dev.get('name'))
    if default_output['name'] in dev.get('name') and "[Loopback]" in dev.get('name'):
        print (f"This is default device from array {dev.get('name')} at index {i}")
        dev_index = i   #assign dev index to current index



print(dev_index)    #personal check of dev index
CHUNK = 2**11       #num of data points read at one time
RATE = 48000        #time resolution of the recording device (Hz)
CHANNELS = 2        #stereo usually has 2 channels
maxValue = 2**15
bars = 50        



#code below is for terminal visualization


#start streaming
stream=p.open(format=pyaudio.paInt16,channels=CHANNELS, rate=RATE, input=True, input_device_index=dev_index, frames_per_buffer=CHUNK)

while True:
    data = np.frombuffer(stream.read(1024),dtype=np.int16)
    dataL = data[0::2]
    dataR = data[1::2]
    peakL = np.abs(np.max(dataL)-np.min(dataL))/maxValue
    peakR = np.abs(np.max(dataR)-np.min(dataR))/maxValue
    lString = "#"*int(peakL*bars)+"-"*int(bars-peakL*bars)
    rString = "#"*int(peakR*bars)+"-"*int(bars-peakR*bars)
    print("L=[%s]\tR=[%s]"%(lString, rString))



'''

#Loop for a few seconds, putting #'s for peaking in bars. This is the visualization
for i in range(int(2048)):
    data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
    peak=np.average(np.abs(data))*4
    bars="#"*int(50*peak/2**16)
    print("%04d %05d %s"%(i,peak,bars))
'''


#close programs
stream.stop_stream()
stream.close()
p.terminate()

