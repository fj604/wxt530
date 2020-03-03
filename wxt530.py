#!/usr/bin/python3

import argparse
import serial
import json
import sys

import paho.mqtt.client as mqtt

argparser = argparse.ArgumentParser()
argparser.add_argument("-p", "--port", default="/dev/ttyUSB0", help="Serial port")
argparser.add_argument("-b", "--baud", default=9600, type=int, help="Baud rate")
argparser.add_argument("-j", "--json", action="store_true", help="JSON output")
argparser.add_argument("-m", "--mqtt", default="localhost", help="MQTT broker hostname")
argparser.add_argument("-t", "--topic", type=str, help="MQTT topic")

args = argparser.parse_args()

port = args.port
baudrate = args.baud
timeout = 60


header = "$WIXDR"

t = {}

t['A'] = {0: "Wind direction min", 1: "Wind direction average", 2: "Wind direction max"}
t['S'] = {0: "Wind speed min", 1: "Wind speed average", 2: "Wind speed max"}
t['P'] = {0: "Pressure"}
t['C'] = {0: "Air temperature", 1: "Internal temperature", 2: "Heating temperature", 3: "Aux. temperature (pt1000)"}
t['H'] = {0: "Relative humidity"}
t['V'] = {0: "Rain accumulation", 1: "Hail accumulation"}
t['Z'] = {0: "Rain duration", 1: "Hail duration"}
t['R'] = {0: "Rain current intensity", 1: "Hail current intensity", 2: "Rain peak intensity", 3: "Hail peak intensity"}
t['U'] = {0: "Supply voltage", 1: "Heating voltage", 2: "3.5 V reference voltage", 3: "Solar radiation", 4: "Ultrasonic level sensor"}
t['G'] = {4: "Information field"}

u = {}

u['C'] = {'C': "Celsius", 'F': "Fahrenheit"}
u['A'] = {'D': "degrees"}
u['S'] = {'K': "km/h", 'M': "m/s", 'N': "knots", 'S': "mph"}
u['P'] = {'B': "bars", 'P': "Pascal", 'H': "hPa", 'I': "inHg", 'M': "mmHg" }
u['H'] = {'P': "Percent"}
u['V'] = {'M': "mm", 'I': "in", 'H': "hits"}
u['Z'] = {'S': "seconds"}
u['R'] = {'M': "mm/h", 'I': "in/h", 'H': "hits/h"}
u['U'] = {'V': "volts", 'N': "n/a"}
u['G'] = {'P': "Percent"}
u['G'] = {'': ""}


if args.topic is not None:
    client = mqtt.Client()
    client.connect(args.mqtt)
    client.loop_start()

with serial.Serial(port, baudrate, timeout=timeout) as file:
    while True:
        try:
            line = file.readline().decode().strip()
        except UnicodeDecodeError:
            line = ""
        elements = line.split('*')
        data = elements[0]
        try:
            checksum = elements[1]
        except IndexError:
            checksum = ""
        items = data.split(",")
        if items[0] == header:
            i = 1
            m = []
            while i < len(items):
                t_type = items[i]
                try:
                    data = float(items[i + 1])
                except ValueError:
                    data = 0
                units = items[i + 2].upper()
                t_id = int(items[i + 3])
                m.append({"measurement": t[t_type][t_id], "data": data, "units": u[t_type][units]})
                if not args.json:
                    print(t[t_type][t_id], data, u[t_type][units])
                i += 4
            if args.json:
                print(json.dumps(m))
            if args.topic is not None:
                for measurement in m:
                    topic = args.topic + "/" + measurement["measurement"].replace(' ', '_')
                    client.publish(topic, measurement["data"])
            sys.stdout.flush()
