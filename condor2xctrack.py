# -*- coding: utf-8 -*-
"""Condor2 to XCTrack UDP Connector

This script enables using the Condor2 NMEA interface as a
basic external sensor with XCTrack.

To this end, the script forwards Condor2 NMEA sentences received via
the serial interface to the given UDP server.

The following NMEA sentence manipulations are applied before forwarding:
- Change GPRMC message to contain the date field value (field 9).

  Condor2 (version 2.1.8) does not include the date field in the GPRMC
  sentence, which causes XCTrack-side parsing to fail. The script adjusts
  the GPRMC fields accordingly.

Example:
        Given XCTrack UDP server IP 192.168.1.123 and com0com
        virtual COM port "\\.\CNCB0", the script is started as
        follows.

        $ python condor2xctrack.py 192.168.1.123 \\.\CNCB0
"""

import argparse
import re
import socket
import sys
from dataclasses import dataclass
from datetime import datetime

import serial

# default XCTrack UDP server port
DEFAULT_UDP_SERVER_PORT = 10110

# default baud rate of the source serial port (115200-8-N-1)
DEFAULT_SERIAL_BAUDRATE = 115200

# for the time being we only touch the RMC sentence
# see http://www.nmea.de/nmea0183datensaetze.html#rmc
RMC_DATE_FIELD_INDEX = 9


@dataclass
class NmeaSentence:
    NMEA_MSG_PATTERN = r"\$([^\*]+)\*([\w]+)\s*"

    items: list

    @property
    def record_id(self):
        return self.items[0]

    @property
    def crc(self):
        data = self._items_str
        crc = 0
        for v in data:
            crc ^= ord(v)
        return f"{crc:02X}"

    @property
    def _items_str(self):
        return ",".join(self.items)

    @classmethod
    def from_str(cls, msg):
        m = re.match(NmeaSentence.NMEA_MSG_PATTERN, msg)
        if not m:
            raise ValueError(f"Could not parse message '{msg}'")

        items = m.group(1).split(",")
        crc = m.group(2)

        nmea = NmeaSentence(items=items)
        if nmea.crc != crc:
            raise ValueError(
                f"Invalid CRC for message '{msg}' (expected: {nmea.crc}, actual: {crc})"
            )

        return nmea

    def to_str(self):
        return f"${self._items_str}*{self.crc}\r\n"


def process_nmea(config):
    out_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    with serial.Serial(config.serial_port, config.serial_baudrate, timeout=1) as ser:
        print("NMEA connector started (press Ctrl-c to stop)...")
        while True:
            msg = ser.readline()
            if not msg:
                continue

            # pass through all NMEA sentences without furhter processing
            # except the ones we need to touch
            if msg.startswith(b"$GPRMC,"):
                m = NmeaSentence.from_str(msg.decode("ascii"))
                if m.record_id == "GPRMC":
                    # add missing date field in Condor2 NMEA RMC message
                    m.items.insert(
                        RMC_DATE_FIELD_INDEX,
                        datetime.utcnow().date().strftime("%d%m%y"),
                    )
                msg = m.to_str().encode("ascii")

            out_socket.sendto(msg, (config.udp_server_ip, config.udp_server_port))
            # print(msg)


def main():
    parser = argparse.ArgumentParser(
        prog="Condor2 to XCTrack UDP connector",
        description="Forward Condor2 NMEA messages to XCTrack UDP server",
    )

    parser.add_argument(
        "udp_server_ip",
        metavar="XCTRACK_IP",
        help="XCTrack target IP address (UDP server)",
    )
    parser.add_argument(
        "--udp_server_port",
        metavar="XCTRACK_PORT",
        type=int,
        default=DEFAULT_UDP_SERVER_PORT,
        help="XCTrack target UDP port",
    )
    parser.add_argument(
        "serial_port",
        metavar="CONDOR_SERIAL_INTERFACE",
        help="Serial port used for receiving Condor NMEA data",
    )
    parser.add_argument(
        "--serial_baudrate",
        metavar="CONDOR_SERIAL_BAUDRATE",
        type=int,
        default=DEFAULT_SERIAL_BAUDRATE,
        help="Serial port baudrate",
    )
    args = parser.parse_args()

    try:
        return process_nmea(args)
    except KeyboardInterrupt:
        return 0
    finally:
        print("NMEA connector stopped...")


if __name__ == "__main__":
    sys.exit(main())
