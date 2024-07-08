from WF_SDK import device, scope, wavegen, tools, error
import numpy as np
import matplotlib.pyplot as plt
import ctypes
from sys import platform
from os import sep
from time import sleep


if platform.startswith("win"):
    dwf = ctypes.cdll.dwf
elif platform.startswith("darwin"):
    dwf = ctypes.cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = ctypes.cdll.LoadLibrary("libdwf.so")

# Pulse parameters
pulse_amplitude = 300e-3  # 300 mV
pulse_width = 700e-9
tau_rise = 100e-9
tau_fall = 200e-9

# Time vector
t = np.linspace(0, 3*pulse_width, 1000)

# Modified Gaussian function
def pulse(t, amplitude, tau_rise, tau_fall):
    p = (1 - np.exp(-t/tau_rise)) * np.exp(-t/tau_fall)
    return -amplitude * p / np.max(np.abs(p))  # fixed code but only 70% effective whatever amplitude I set

# Generate pulse data
pulse_data = pulse(t, pulse_amplitude, tau_rise, tau_fall)

# # Plot the pulse
# plt.figure(figsize=(10, 6))
# plt.plot(t*1e9, pulse_data*1e3, label=f"{pulse_width*1e9:.0f} ns, {pulse_amplitude*1e3:.0f} mV")
# plt.xlabel('Time (ns)')
# plt.ylabel('Voltage (mV)')
# plt.title('Inverted Simulated PMT Pulse Output')
# plt.grid(True)
# plt.legend()
# plt.show()

try:
    # Enumerate devices
    device_count = ctypes.c_int()
    dwf.FDwfEnum(scope.constants.enumfilterAll, ctypes.byref(device_count))

    if device_count.value == 0:
        raise error("No device found")

    # Open the first device
    hdwf = ctypes.c_int()
    dwf.FDwfDeviceOpen(ctypes.c_int(0), ctypes.byref(hdwf))

    # Prepare the device data structure
    device_data = device.data()
    device_data.handle = hdwf.value

    # Initialize the wavegen with default settings
    wavegen.enable(device_data, channel=1)

    # Prepare the pulse data for the wavegen
    mydata = (ctypes.c_double * len(pulse_data))(*pulse_data)

    # Configure the wavegen to output the pulse
    wavegen.dwf.FDwfAnalogOutNodeEnableSet(device_data.handle, ctypes.c_int(0), wavegen.constants.AnalogOutNodeCarrier, ctypes.c_bool(True))
    wavegen.dwf.FDwfAnalogOutNodeFunctionSet(device_data.handle, ctypes.c_int(0), wavegen.constants.AnalogOutNodeCarrier, wavegen.constants.funcCustom)
    wavegen.dwf.FDwfAnalogOutNodeDataSet(device_data.handle, ctypes.c_int(0), wavegen.constants.AnalogOutNodeCarrier, mydata, ctypes.c_int(len(pulse_data)))
    wavegen.dwf.FDwfAnalogOutNodeFrequencySet(device_data.handle, ctypes.c_int(0), wavegen.constants.AnalogOutNodeCarrier, ctypes.c_double(1 / (pulse_width)))
    wavegen.dwf.FDwfAnalogOutNodeAmplitudeSet(device_data.handle, ctypes.c_int(0), wavegen.constants.AnalogOutNodeCarrier, ctypes.c_double(pulse_amplitude))
    wavegen.dwf.FDwfAnalogOutConfigure(device_data.handle, ctypes.c_int(0), ctypes.c_bool(True))

    print("Generating pulse...")

    # Keep the waveform running for 20 secs
    sleep(20) 

    # Stop the waveform
    wavegen.dwf.FDwfAnalogOutConfigure(device_data.handle, ctypes.c_int(0), ctypes.c_bool(False))

    # Close the device
    dwf.FDwfDeviceClose(hdwf)
    print("Pulse generation done!")
except error as e:
    print(e)
    # Ensure the device is closed in case of error
    dwf.FDwfDeviceCloseAll()