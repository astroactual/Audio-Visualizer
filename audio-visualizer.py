import pyaudio
import struct #unpacks audio data into integers
import numpy as np
import matplotlib.pyplot as plt

%matplotlib tk

CHUNK = 1024 * 4            #decides how much audio processed per frame
FORMAT = pyaudio.paInt16    #bytes per sample
CHANNELS = 1                #how many audio channels, for now 1 is just audio out
RATE = 44100                #sample rate per second, common is 44.1kHz


p = pyaudio.PyAudio()       #main pyAudio object

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK
)



fig, ax = plt.subplots()

x = np.arange(0, 2 * CHUNK, 2)
line, = ax.plot(x, np.random.rand(CHUNK))
ax.set_ylim(0,500)
ax.set_xlim(0,CHUNK)


while True:
    data = stream.read(CHUNK)
    data_int = np.array(struct.unpack(str(2 * CHUNK) + 'B', data), dtype=np.int16)[::2] + 127
    line.set_ydata(data_int)
    fig.canvas.draw()
    fig.canvas.flush_events()








