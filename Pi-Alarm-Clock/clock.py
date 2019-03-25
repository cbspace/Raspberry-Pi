#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to display alarm clock on
128x64 graphical LCD screen.
Also displays my weather station data
"""

import datetime
import math
import pylcd
import sys
import time
import wiringpi

import httplib
import urllib

PINMAP = {
	'RS': 17,
	'E': 27,
	'D0': 22,
	'D1': 23,
	'D2': 24,
	'D3': 10,
	'D4': 9,
	'D5': 25,
	'D6': 8,
	'D7': 11,
	'CS1': 7,
	'CS2': 5,
	'RST': 6,
	'LED': 18,
}

WEEKDAYS = (
	"Mon",
	"Tue",
	"Wed",
	"Thu",
	"Fri",
	"Sat",
	"Sun",
)

display_scroll = False;

temperature = 0.0;
humidity = 0.0;

def get_temp():
	try:
		global temperature
		conn = httplib.HTTPConnection("wilstonweather.cbrennan.space:80")
		conn.request("GET", "/api/v1/current/temp")
		response = conn.getresponse()
		temperature = round(float(response.read()),1)
		conn.close()
	except:
		print "Can not get Temperature"
		
def get_humidity():
	try:
		global humidity
		conn = httplib.HTTPConnection("wilstonweather.cbrennan.space:80")
		conn.request("GET", "/api/v1/current/humidity")
		response = conn.getresponse()
		humidity = round(float(response.read()),0)
		conn.close()
	except:
		print "Can not get Humidity"

def alarm():
	for x in range(10):
		state = 1
		wiringpi.digitalWrite(16,state)
		wiringpi.delay(50)
	
		state = 0
		wiringpi.digitalWrite(16,state)
		wiringpi.delay(200)
		
		state = 1
		wiringpi.digitalWrite(16,state)
		wiringpi.delay(50)
		
		state = 0
		wiringpi.digitalWrite(16,state)
		wiringpi.delay(700)

def main():
	display = pylcd.ks0108.Display(backend = pylcd.GPIOBackend, pinmap = PINMAP, debug = False)
	draw = pylcd.ks0108.DisplayDraw(display)
	display.commit(full = True)
	old_minute = -1
	
	# Set up buzzer pin
	wiringpi.pinMode(16,1)
	
	while True:
		now = datetime.datetime.now()
		
		if now.minute != old_minute:
			old_minute = now.minute
			
			get_temp()
			get_humidity()
			
			# 0 = No Brightness, 1023 = Full Brightness
			if now.hour >= 21 and now.hour < 22:
				display.set_brightness(400)
			elif now.hour >= 22:
				display.set_brightness(32)
			elif 0 <= now.hour < 6:
				display.set_brightness(16)
			else:
				display.set_brightness(1023)

			display.clear()
			draw.text("%2i.%02i" % (int(now.strftime("%I")),now.minute), 'center', 'top', 52, "/home/pi/code/clock/fonts/timesbd.ttf")
			draw.text("%.1fC %.0f%%" % (temperature,humidity), 'center', ('bottom', 0, 61), 26, "/home/pi/code/clock/fonts/timesbd.ttf")

			display.commit()
			time_needed = (datetime.datetime.now() - now).total_seconds()
			
			# Check if we need to sound the alarm
			#if now.weekday() <= 4:
				#if now.hour == 7:
					#if now.minute == 00 or now.minute == 15:
						#alarm()
			
		time.sleep(5)

if __name__ == "__main__":
	main()
