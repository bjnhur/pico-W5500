import gc
import board
import busio
import digitalio
import time
from adafruit_wiznet5k.adafruit_wiznet5k import *
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import neopixel


class OKError(Exception):
    """The exception thrown when we didn't get acknowledgement to an AT command"""

SPI1_SCK = board.GP10
SPI1_TX = board.GP11
SPI1_RX = board.GP12
SPI1_CSn = board.GP13
W5500_RSTn = board.GP15
UART0_TX = board.GP16
UART0_RX = board.GP17

print("Wiznet5k AX1 Loopback Test (DHCP)")
# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x01, 0x02, 0x03, 0x04, 0x05)

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

# # Initialize ethernet interface without DHCP
# eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=MY_MAC, debug=False)
# # Set network configuration
# eth.ifconfig = (IP_ADDRESS, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER)

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)

print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Initialize a socket for our server
socket.set_interface(eth)
server = socket.socket()  # Allocate socket for the server
server_ip = None  # IP address of server
server_port = 50007  # Port to listen on
server.bind((server_ip, server_port))  # Bind to IP and Port
server.listen()  # Begin listening for incoming clients
print("server listen")

###################################
# WizFi360 related code & functions

uart = busio.UART(tx=UART0_TX, rx=UART0_RX, baudrate=115200, timeout=0.5)
_ipdpacket = bytearray(1500)

# from adafruit_espatcontrol.py, https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol/blob/main/adafruit_espatcontrol/adafruit_espatcontrol.py
def at_response(at_cmd, timeout=2.0, retries=1, _debug=True):
    """Send an AT command, check that we got an OK response,
    and then cut out the reply lines to return. We can set
    a variable timeout (how long we'll wait for response) and
    how many times to retry before giving up"""
    # pylint: disable=too-many-branches
    for _ in range(retries):
        time.sleep(0.1)  # wait for uart data
        uart.reset_input_buffer()  # flush it
        if _debug:
            print("--->", at_cmd)
        uart.write(bytes(at_cmd, "utf-8"))
        uart.write(b"\x0d\x0a")
        stamp = time.monotonic()
        response = b""
        while (time.monotonic() - stamp) < timeout:
            if uart.in_waiting:
                response += uart.read(1)
                if response[-4:] == b"OK\r\n":
                    break
                if response[-7:] == b"ERROR\r\n":
                    break
                # if "AT+CWJAP=" in at_cmd:
                #     if b"WIFI GOT IP\r\n" in response:
                #         break
                # else:
                #     if b"WIFI CONNECTED\r\n" in response:
                #         break
                # if b"ERR CODE:" in response:
                #     break
        # eat beginning \n and \r
        if _debug:
            print("<---", response)
        # special case, AT+CWJAP= does not return an ok :P
        if "AT+CWJAP=" in at_cmd and b"WIFI GOT IP\r\n" in response:
            return response
        # special case, ping also does not return an OK
        if "AT+PING" in at_cmd and b"ERROR\r\n" in response:
            return response
        if response[-4:] != b"OK\r\n":
            time.sleep(1)
            continue
        return response[:-4]
    time.sleep(1)
# raise OKError("No OK response to " + at_cmd)

# Get the code, socket_send() function from adafruit_espatcontrol.py, https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol/blob/main/adafruit_espatcontrol/adafruit_espatcontrol.py
# Change the name to wizfi360_socket_send() & modify some.
def wizfi360_socket_send(buffer, timeout=1, _debug=True):
    """Send data over the already-opened socket, buffer must be bytes"""
    cmd = "AT+CIPSEND=%d" % len(buffer)
    at_response(cmd, timeout=5, retries=1)
    prompt = b""
    stamp = time.monotonic()
    while (time.monotonic() - stamp) < timeout:
        if uart.in_waiting:
            prompt += uart.read(1)
            # print(prompt)
            if prompt[-1:] == b">":
                break
    if not prompt or (prompt[-1:] != b">"):
        raise OKError("Didn't get data prompt for sending")
    uart.reset_input_buffer()
    uart.write(buffer)
    stamp = time.monotonic()
    response = b""
    while (time.monotonic() - stamp) < timeout:
        if uart.in_waiting:
            response += uart.read(uart.in_waiting)
            if response[-9:] == b"SEND OK\r\n":
                break
            if response[-7:] == b"ERROR\r\n":
                break
    if _debug:
        print("<---", response)
    # Get newlines off front and back, then split into lines
    return True

# Get the code, socket_receive() function from adafruit_espatcontrol.py, https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol/blob/main/adafruit_espatcontrol/adafruit_espatcontrol.py
# Change the name to wizfi360_socket_receive() & modify some.
def wizfi360_socket_receive(timeout=5, _debug=True):
    # pylint: disable=too-many-nested-blocks, too-many-branches
    """Check for incoming data over the open socket, returns bytes"""
    incoming_bytes = None
    bundle = []
    toread = 0
    gc.collect()
    i = 0  # index into our internal packet
    stamp = time.monotonic()
    ipd_start = b"+IPD,"
    while (time.monotonic() - stamp) < timeout:
        if uart.in_waiting:
            stamp = time.monotonic()  # reset timestamp when there's data!
            if not incoming_bytes:
                # hw_flow(False)  # stop the flow
                # read one byte at a time
                _ipdpacket[i] = uart.read(1)[0]
                if chr(_ipdpacket[0]) != "+":
                    i = 0  # keep goin' till we start with +
                    continue
                i += 1
                # look for the IPD message
                if (ipd_start in _ipdpacket) and chr(
                    _ipdpacket[i - 1]
                ) == ":":
                    try:
                        ipd = str(_ipdpacket[5 : i - 1], "utf-8")
                        incoming_bytes = int(ipd)
                        if _debug:
                            print("Receiving:", incoming_bytes)
                    except ValueError as err:
                        raise RuntimeError(
                            "Parsing error during receive", ipd
                        ) from err
                    i = 0  # reset the input buffer now that we know the size
                elif i > 20:
                    i = 0  # Hmm we somehow didnt get a proper +IPD packet? start over

            else:
                # hw_flow(False)  # stop the flow
                # read as much as we can!
                toread = min(incoming_bytes - i, uart.in_waiting)
                # print("i ", i, "to read:", toread)
                _ipdpacket[i : i + toread] = uart.read(toread)
                i += toread
                if i == incoming_bytes:
                    # print(_ipdpacket[0:i])
                    gc.collect()
                    bundle.append(_ipdpacket[0:i])
                    gc.collect()
                    i = incoming_bytes = 0
                    break  # We've received all the data. Don't wait until timeout.
        else:  # no data waiting
            # hw_flow(True)  # start the floooow
            pass
    totalsize = sum([len(x) for x in bundle])
    ret = bytearray(totalsize)
    i = 0
    for x in bundle:
        for char in x:
            ret[i] = char
            i += 1
    for x in bundle:
        del x
    gc.collect()
    return ret

def recvUART(timeout=1.0, _debug=True):
    stamp = time.monotonic()
    response = b""
    while (time.monotonic() - stamp) < timeout:
        if uart.in_waiting:
            response += uart.read(1)
    # eat beginning \n and \r
    if _debug:
        print("<---", response)
    return response

#################################################
# WizFi360 Initialization & setting

at_response('AT') #AT
at_response('AT+RST') #AT
at_response('AT+CWAUTOCONN=0') #auto con disable
at_response('AT+GMR') #firmware ver
# AT+GMR
# AT version:1.1.1.7(May  4 2021 15:14:59)
# SDK version:3.2.0(a0ffff9f)
# compile time:May  4 2021 15:14:59

# OK
at_response('AT+CWMODE_CUR=1')
at_response('AT+CWQAP')
at_response('AT+CWDHCP_CUR=1,1')
at_response('AT+CWJAP_CUR="twlab","twlab0104!"') #AP connecting
# AT+CWJAP_CUR="twlab","twlab0104!"
# WIFI DISCONNECT
# WIFI CONNECTED
# WIFI GOT IP

# OK
time.sleep(0.5)
at_response('AT+CIPSTA_CUR?') #network chk
# AT+CIPSTA_CUR?
# +CIPSTA_CUR:ip:"192.168.0.20"
# +CIPSTA_CUR:gateway:"192.168.0.1"
# +CIPSTA_CUR:netmask:"255.255.255.0"

# OK
at_response('AT+CIPSTART="TCP","192.168.0.8",5001')
# AT+CIPSTART="TCP","192.168.0.8",5001
# CONNECT

# OK

#################################################
# W5K Eth <-> WizFi360 Echo main loop

conn = None
rbuf_wizfi360 = b""
rbuf_w5k = b""

while True:
    # Maintain DHCP lease
    eth.maintain_dhcp_lease()

    if conn is None:
        conn, addr = server.accept()  # Wait for a connection from a client.
        print("\r\nW5K socket connected\r\n")
        print(conn, addr)
    else :
        if conn.status in (
            SNSR_SOCK_FIN_WAIT,
        ):
            print("socket SNSR_SOCK_FIN_WAIT")
            conn.close()
            conn = None
        elif conn.status in (
            SNSR_SOCK_CLOSE_WAIT,
        ):
            print("socket SNSR_SOCK_CLOSE_WAIT")
            conn.disconnect()
            conn.close()
            conn = None
        else :
            # print("socket established", conn.status)
            avail = conn.available()
            if avail:
                # print("Received size:", avail)
                # rbuf_w5k = conn.recv(0)
                rbuf_w5k = conn.embed_recv(0)
                if rbuf_w5k:
                    print("recv rbuf_w5k from W5K:",rbuf_w5k)
                    wizfi360_socket_send(rbuf_w5k) # Echo message back to WizFi360
                    print("Data sent to WizFi360\r\n")
                rbuf_w5k = b""

    if uart.in_waiting:
        # rbuf_wizfi360 = recvUART(0.5)
        rbuf_wizfi360 = wizfi360_socket_receive(0.5)
        print("recv data from WizFi360:",rbuf_wizfi360)
        if conn:
            conn.send(rbuf_wizfi360)  # Echo message back to W5K client
            print("Data sent to W5K\r\n")
        rbuf_wizfi360 = b""
