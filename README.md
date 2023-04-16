# Condor2 to XCTrack UDP Connector

Simple script to use Condor2 (https://www.condorsoaring.com/) as an external
sensor with XCTrack.

This script retrieves NMEA messages received from Condor2 on a virtual COM port
and forwards them to XCTrack (UDP server). Before forwarding, the received NMEA
messages are manipulated to be valid XCTrack sensor input.

## Prerequisites

The script is expected to run on the same host as the Condor2 soaring simulator,
while the XCTrack application is executed on another device (e.g. smartphone) in the
same network as the host running Condor2.

NOTE: This connector is not fully tested, experiments were done using Windows 11,
      com0com virtual COM port driver, Condor version 2.1.8, XCTrack version 0.9.8.6.

## Installation

1. Install Python3 (>=3.10), e.g. via the Microsoft Store.
2. Install a virtual serial port driver, e.g. com0com (https://com0com.sourceforge.net/).

   See also https://www.condorsoaring.com/forums/viewtopic.php?t=12538

3. Install Python package dependencies (in a Python virtual environment).

   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Configure Condor2 to send NMEA messages to the virtual COM port.
   
   Setup -> Options -> NMEA output: Enable and set port accordingly (e.g. CNCA0 with com0com).

2. Configure XCTrack to use external sensors.

   1. Enter Settings -> Connections and Sensors.
   2. Enable External Sensors -> UDP server.
   3. Note down the network port (by default 10110).
   4. Enable (at least) use of external GPS and use of external flight speed.

## Usage

Start XCTrack, Condor2 and run the Python script.

```
python condor2xctrack.py [--udp_server_port <XCTrack UDP port>] <XCTrack device IP> <Condor2 serial port> 
```

### Example

XCTrack device IP: 192.168.1.123, XCTrack server port: default (10110), Condor2 COM port: CNCB0 (com0com)

```
python condor2xctrack.py 192.168.1.123 \\.\CNCB0
```
