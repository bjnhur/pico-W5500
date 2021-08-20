import board
import busio
import digitalio
import time
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import adafruit_requests as requests
import adafruit_wiznet5k.adafruit_wiznet5k_wsgiserver as server
from adafruit_wsgi.wsgi_app import WSGIApp
import neopixel

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

pixel_pin = board.GP3
num_pixels = 2

print("Wiznet5k Web Server Test (DHCP)")

# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)
# # Set manual network configuration
# IP_ADDRESS = (192, 168, 0, 111)
# SUBNET_MASK = (255, 255, 0, 0)
# GATEWAY_ADDRESS = (192, 168, 0, 1)
# DNS_SERVER = (8, 8, 8, 8)

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
# # Set manual network configuration
# eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=False)

# Initialize a requests object with a socket and ethernet interface
requests.set_socket(socket, eth)

# Here we create our application, registering the
# following functions to be called on specific HTTP GET requests routes
web_app = WSGIApp()

html_string = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RaspberryPi Pico Web server - WIZnet W5100S/W5500</title>
</head>
<body>
<div align="center">
<H1>Welcome! RaspberryPi Pico Web server</H1>
<h2>Network Information</h2>
<p>
Chip Version is $CHIPNAME<br>
My IP address is $IPADDRESS<br>
</p>
<h2>Control LED color</h2>
<p>
<label for="colorWell">Color Select: </label><input type="color" value="#000000" id="colorWell"><a href="/led/000000" id="change_color"> -> Change Color</a>
</p>
<h2>View file example</h2>
<p>
<a href="/code">View code.py</a>
</p>
<h2>Getting JSON data example</h2>
<p>
<a href="/btc">currentprice/USD.json</a>
</p>
<h2>Go to root</h2>
<p>
<a href="/">root page</a>
</p>
</div>
<script>
var colorWell;
var defaultColor = "#000000";
window.addEventListener("load", startup, false);
function startup() {
colorWell = document.querySelector("#colorWell");
colorWell.value = defaultColor;
colorWell.addEventListener("change", updateAll, false);
colorWell.select();
}
function updateAll(event) {
var iLen = String(event.target.value).length;
document.getElementById("change_color").href="/led/" + String(event.target.value).substring(1, iLen);
}
</script>
</body>
</html>
'''

html_string = html_string.replace("$CHIPNAME",eth.chip)
html_string = html_string.replace("$IPADDRESS",eth.pretty_ip(eth.ip_address))

@web_app.route("/led/<color>")
def led_on(request, color):  # pylint: disable=unused-argument
    print("LED handler")
    color_value = int(color, 16)
    pixels.fill(color_value)
    pixels.show()
    html_string_led = html_string.replace("#000000", "#"+color)
    # return ("200 OK", [], [f"LED set! {r}{g}{b} "])
    return ("200 OK", [], [html_string_led])

@web_app.route("/")
def root(request):  # pylint: disable=unused-argument
    print("Root WSGI handler")
    # return ("200 OK", [], ["Root document"])
    return ("200 OK", [], [html_string])

@web_app.route("/large")
def large(request):  # pylint: disable=unused-argument
    print("Large pattern handler")
    return ("200 OK", [], ["*-.-" * 2000])

@web_app.route("/code")
def code(request):  # pylint: disable=unused-argument
    print("Static file code.py handler")
    return ("200 OK", [], get_static_file("code.py"))
    # response_str = ""
    # for newbyte in get_static_file("code.py"):
    #     response_str += str(newbyte)
    # return ("200 OK", [], [response_str])

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
