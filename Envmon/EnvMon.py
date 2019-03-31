# Environment Monitor Python Code
# Receives data from EnvMon, processes data and posts data to web
# Also logs errors to log.txt file
# By Craig Brennan

CONST_VERSION = 3.8

import sys
import serial
import string
import time
import httplib
import urllib
import json
import os

from BMP085 import BMP085

# Constants
temperature_position = 0	# Temperature list reference
wind_position = 1			# Wind speed list reference
rain_position = 2			# Rain list reference
humidity_position 	 = 3	# Humidity list reference

# How often to update server (x 5 seconds)
WEB_COUNT_MAX = 60

# Function to append text to the log file
# Also prints to the terminal if second parameter is true
def loggit(text,t):
	
	#Open file
	f = open('/home/pi/EnvMon/logs/log.txt','a')
	
	# Write to file
	try:
		f.write(time.strftime('%Y-%m-%d %X') + ': ' + text + '\r\n')
		f.flush()
	except:
		print 'Error writing to log file'
	finally:
		# Ensure file is closed if an error occurs
		f.close()
	# Print to terminal if required
	if t == True:
		print text

# Lg initialisation of script
loggit('Script initiated',False)

# Print opening message
print "Envmon Python Script V" + str(CONST_VERSION)
print

# Open Serial Connection
try:
	ser = serial.Serial("/dev/ttyAMA0", 4800)
except:
	loggit('Serial port open error',True)

# Open BMP085 Pressure Sensor Connection
bmp = BMP085()

# Accumulated Total
temperature_total = 0
humidity_total = 0
pressure_total = 0

# Is this this first count?
first_count = True

# Sample counter used to take sample every 5 seconds
sample_counter = 1 

# Web counter used to update web every 1 minute
web_counter = 1 

# Boolean used to indicate if web is up to date
up_to_date = True

# Future
wind = 0;
wind_dir = 0;

# Save data to file - Used when web is offline
def save_offline(currenttime,temperature,wind,rain,humidity,pressure,wind_dir):

	# Set boolean to false to indicate web is not up to date
	global up_to_date
	up_to_date = False

	# Create Dictionary and convert to string
	data = { 'Time':currenttime, 'Temp':temperature, 'Wind':wind, 'Rain':rain, 'Hmdt':humidity, 'Press':pressure, 'WDir':wind_dir }
	data_string = json.dumps(data,sort_keys=False)
	
	# Open File and append data
	f = open('/home/pi/EnvMon/logs/offline_data.txt','a+')
	f.write(data_string + '\r\n')
	f.close()
	
# Transmit data from file to server
def update_server():
	
	global up_to_date
	
	# Open File and load data
	f = open('/home/pi/EnvMon/logs/offline_data.txt','r')

	while True:
		# Read a line from the file and strip cr + lf
		data = f.readline()
		data = data.rstrip()
		
		# If we reach the end then break
		if not data: break
		json_data = json.loads(data)
		
		# Sleep for one second so that we don't overload server
		time.sleep(1)
		
		print 'Updating server - ', json_data['Time']
		
		# Update web
		try:
			params = urllib.urlencode({'timestamp': json_data['Time'], 'temperature': json_data['Temp'], 'humidity': json_data['Hmdt'],
			'pressure': json_data['Press'], 'rain': json_data['Rain'], 'wind': json_data['Wind'], 'wind_dir': json_data['WDir']})
			headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
			conn = httplib.HTTPConnection("wilstonweather.cbrennan.space:80")
			conn.request("POST", "/update.php", params, headers)
			response = conn.getresponse()
			conn.close()
		except:
			loggit('HTTP Connection Error during server update, data will be lost!',True)
			# Note: if an error occurs here the data will be lost as there is no contingency
		else:	
			print response.status, response.reason
			print
    
	# Close and delete file
	f.close()
	os.remove('/home/pi/EnvMon/logs/offline_data.txt')
	
	# We are now up to date
	up_to_date = True
	loggit('Web is now up to date',True)

# Update web. If web is not available then save to file 'offline_data.txt'
def update_web():
	# Define globals
	global temperature, temperature_total, humidity, humidity_total, pressure, pressure_total, up_to_date
	
	# Calcualte average values
	temperature = temperature_total / float(WEB_COUNT_MAX)
	humidity = humidity_total / float(WEB_COUNT_MAX)
	pressure = pressure_total / float(WEB_COUNT_MAX)
	
	# Round values to 2 decimal places
	temperature = round(temperature,2)
	humidity = round(humidity,2)
	pressure = round(pressure,3)
	
	# Calculate time
	currenttime = time.strftime('%Y-%m-%d %X')

	# Print messages
	print currenttime
	print "Temperature =",temperature, "degrees C"
	print "Humidity =", humidity, "%"
	print "Rain =", rain_data, "mm"
	print "Pressure =", pressure, "hPa"
	print "Wind Speed =", wind, "km/h"
	print "Wind Direction =", wind_dir
				
	# Update web
	try:
		params = urllib.urlencode({'timestamp': currenttime, 'temperature': temperature, 'humidity': humidity,
		'pressure': pressure, 'rain': rain_data, 'wind': wind, 'wind_dir': wind_dir})
		headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
		conn = httplib.HTTPConnection("wilstonweather.cbrennan.space:80")
		conn.request("POST", "/update.php", params, headers)
		response = conn.getresponse()
		conn.close()
	except:
		loggit('HTTP Connection Error!',True)
		# Save data to file
		save_offline(currenttime,temperature,wind,rain_data,humidity,pressure,wind_dir)
	else:
		print response.status, response.reason
		print	
			
		if response.status == 200:
			# Server is up again so transfer the data
			if not up_to_date: update_server()		
		else:
			# Server error, save data offline
			loggit('HTTP Response Error: ' + str(response.status) + ' ' + response.reason,False)
			save_offline(currenttime,temperature,wind,rain_data,humidity,pressure,wind_dir)
			
	# Reset totals
	temperature_total = 0
	humidity_total = 0
	pressure_total = 0

# Main Loop
while True:
	
	# Read a line of data from serial port and ensure length is correct
	while True:
		rx = ser.readline()
		if len(rx) == 22:
			break
	
	# Print string
	print rx.rstrip()
	
	# Only sample every 5 seconds
	if sample_counter == 5:
		
		# Reset sample counter
		sample_counter = 0
	
		# Store data in variables
		try:
			temperature_data = int(rx[5*temperature_position+1:5*temperature_position+5],16)
			humidity_data = int(rx[5*humidity_position+1:5*humidity_position+5],16)
			rain_data = int(rx[5*rain_position+1:5*rain_position+5],16)
		except ValueError, e:
			loggit(e,True)
		else:
	
			# Calculate weather readings
			temperature = temperature_data*0.01 - 39.64
			humidity = (-1.5955*pow(10,-6))*pow(humidity_data,2) + humidity_data*0.0367 - 2.0468
			
			# Update pressure
			bmp.update()
			pressure = bmp.get_pressure()
			
			# Update inside temperature
			inside_temp = bmp.get_temp()
			
			# Display inside temperature
			print
			print "Inside Temperature:", inside_temp, "degrees C"
			print
			
			# If this is not the first count then ensure reading is valid
			if not first_count:
				# Assume data is valid if reading is less than 1 different from last
				if (abs(temperature_previous - temperature) < 2.0) and (abs(humidity_previous - humidity) < 5.0):
					# Update totals
					temperature_total += temperature		
					humidity_total += humidity
					pressure_total += pressure
					
					# Store values for use next time
					temperature_previous = temperature
					humidity_previous = humidity	
					
					# Update web every 5 minutes (60 x 5 second samples)
					if web_counter >=  WEB_COUNT_MAX:
						# Reset web counter and update web
						web_counter = 0
						update_web()
					
					# Increment web counter
					web_counter = web_counter + 1
				else:
					loggit('Invalid data: T(' + str(temperature_previous) + ' to ' + str(temperature) + ') H(' + str(humidity_previous) + ' to ' + str(humidity) + ')',True)
			else:
				# Store values for use next time
				temperature_previous = temperature
				humidity_previous = humidity	
				# Unset flag
				first_count = False	
				
			print "Web counter:", web_counter
			print
				
	# Increment sample counter
	sample_counter = sample_counter + 1

# Close serial connection	
ser.close()

# Close File
f.close()
	
