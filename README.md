# pico-W5500
Add W5500 Ethernet to Raspberry Pi Pico
Add W5100S Driver code

## Usage the code.

1. Open the code.
2. Copy the content to code.py on your RPI Pico board
3. Save & Done :)

## Library

Find and copy adafruit_bus_device & adafruit_requests.mpy file from Adafruit's CircuitPython library bundle matching your version of CircuitPython. Don't copy all files and folder in the library. 
- https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/tag/20210409
- Download adafruit-circuitpython-bundle-6.x-mpy-20210409.zip
- or Download adafruit-circuitpython-bundle-6.x-mpy-20210813
~~- unzip and find adafruit_requests.mpy.~~
- use adafruit_requests.py instead of adafruit_requests.mpy
- from https://github.com/adafruit/Adafruit_CircuitPython_Requests/blob/main/adafruit_requests.py

For adafruit_bus_device, download from below link.
- https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

For adafruit_wiznet5k, download from below link.
- modify version : https://github.com/bjnhur/Adafruit_CircuitPython_Wiznet5k
- original version : https://github.com/adafruit/Adafruit_CircuitPython_Wiznet5k
