import pyaudio
import struct #unpacks audio data into integers
import numpy as np
import matplotlib.pyplot as plt

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

data = stream.read(CHUNK)
data