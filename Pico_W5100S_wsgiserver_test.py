import board
import busio
import digitalio
import time
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import adafruit_requests as requests
import adafruit_wiznet5k.adafruit_wiznet5k_wsgiserver as server
from adafruit_wsgi.wsgi_app import WSGIApp

def get_static_file(filename):
    "Static file generator"
    with open(filename, "rb") as f:
        bytes = None
        while bytes is None or len(bytes) == 2048:
            bytes = f.read(2048)
            yield bytes

SPI1_SCK = board.GP10
SPI1_TX = board.GP11
SPI1_RX = board.GP12
SPI1_CSn = board.GP13
W5500_RSTn = board.GP15

print("Wiznet5k Ping Test (no DHCP)")

# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
IP_ADDRESS = (192, 168, 0, 111)
SUBNET_MASK = (255, 255, 0, 0)
GATEWAY_ADDRESS = (192, 168, 0, 1)
DNS_SERVER = (8, 8, 8, 8)

led = digitalio.DigitalInOut(board.GP25)
led.direction = digitalio.Direction.OUTPUT

ethernetRst = digitalio.DigitalInOut(W5500_RSTn)
ethernetRst.direction = digitalio.Direction.OUTPUT

# For Adafruit Ethernet FeatherWing
cs = digitalio.DigitalInOut(SPI1_CSn)
# For Particle Ethernet FeatherWing
# cs = digitalio.DigitalInOut(board.D5)
spi_bus = busio.SPI(SPI1_SCK, MOSI=SPI1_TX, MISO=SPI1_RX)

# Reset W5500 first
ethernetRst.value = False
time.sleep(1)
ethernetRst.value = True

# Initialize ethernet interface with DHCP
# eth = WIZNET5K(spi_bus, cs)
# Initialize ethernet interface without DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)

# # Set network configuration
# eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Initialize a requests object with a socket and ethernet interface
requests.set_socket(socket, eth)

# Here we create our application, registering the
# following functions to be called on specific HTTP GET requests routes

web_app = WSGIApp()


@web_app.route("/led/<r>/<g>/<b>")
def led_on(request, r, g, b):  # pylint: disable=unused-argument
    print("LED handler")
    # led.fill((int(r), int(g), int(b)))
    return ("200 OK", [], [f"LED set! {r}{g}{b} "])


@web_app.route("/")
def root(request):  # pylint: disable=unused-argument
    print("Root WSGI handler")
    return ("200 OK", [], ["Root document"])


@web_app.route("/large")
def large(request):  # pylint: disable=unused-argument
    print("Large pattern handler")
    return ("200 OK", [], ["*-.-" * 2000])


@web_app.route("/code")
def code(request):  # pylint: disable=unused-argument
    print("Static file code.py handler")
    return ("200 OK", [], get_static_file("code.py"))


@web_app.route("/btc")
def btc(request):
    print("BTC handler")
    r = requests.get("http://api.coindesk.com/v1/bpi/currentprice/USD.json")
    result = r.text
    r.close()
    return ("200 OK", [], [result])

# Here we setup our server, passing in our web_app as the application
server.set_interface(eth)
print(eth.chip)
wsgiServer = server.WSGIServer(80, application=web_app)

print("Open this IP in your browser: ", eth.pretty_ip(eth.ip_address))

# Start the server
wsgiServer.start()
# led[0] = (0, 0, 255)

while True:
    # Our main loop where we have the server poll for incoming requests
    wsgiServer.update_poll()
    # Maintain DHCP lease
    eth.maintain_dhcp_lease()
    # Could do any other background tasks here, like reading sensors

    # check live
    led.value = not led.value
    time.sleep(1)
