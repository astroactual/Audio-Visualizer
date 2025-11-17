
import pyaudiowpatch as pyaudio
import numpy as np
import sounddevice as sd


default_output = sd.query_devices(kind='output')    #find ddefault audio device
print(f"Default: {default_output['name']}")


CHUNK = 2**11       #num of data points read at one time
RATE = 48000        #time resolution of the recording device (Hz)
CHANNELS = 2        #stereo usually has 2 channels



p=pyaudio.PyAudio() #start PyAudio instance


#for all devices connected, compare names. If default device name has the word "Loopback", set as PyAudio device index
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print ( i, dev.get('name'))
    if default_output['name'] in dev.get('name') and "[Loopback]" in dev.get('name'):
        print (f"This is default device from array {dev.get('name')} at index {i}")
        dev_index = i



print(dev_index)    #personal check of dev index



#start streaming
stream=p.open(format=pyaudio.paInt16,channels=CHANNELS, rate=RATE, input=True, input_device_index=dev_index, frames_per_buffer=CHUNK)

#Loop for a few seconds, putting #'s for peaking in bars. This is the visualization
for i in range(int(10*44100/1024)):
    data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
    peak=np.average(np.abs(data))*2
    bars="#"*int(50*peak/2**16)
    print("%04d %05d %s"%(i,peak,bars))


#close programs
stream.stop_stream()
stream.close()
p.terminate()

