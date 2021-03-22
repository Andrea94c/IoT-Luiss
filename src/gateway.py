# Python3.9
# Importiamo le librerie necessarie / Import needed libreries 

# MQTT Protocol per inviare i dati dei sensori all'applicativo online 
# // to send IoT sensor data to the online applicative/dashboard  
import paho.mqtt.client as mqtt

# Serial Protocol per connettersi e riceve dati dai sensori collegati in serial 
# // to connect with the IoT devices on serial ports
import serial 

# Librerie varie per gestire i processi di ricezione dati e la temporizzazione dell'invio dei dati
# Other modules to handle multi-thread e timing in data collection/forward
import json
import time
import threading
import re
import random
from enum import Enum

"""
The class enum to handle the different kind of devices
Una classe Enum per gestire i diversi dispotivi (RaspPico e STM32)
"""
class DeviceType(Enum):
	RaspPICO = 1
	STM = 2
	
# Parametri di connessione MQTT
# MQTT connection parameters
MQTT_TOKEN = "......"  # TODO: inserire il token corretto 
MQTT_HOST = "demo.thingsboard.io"
# Parametri messaggi MQTT / MQTT message field 
ATTRIBUTES = {"firmware_version":"1.0.1", "serial_number":"SN-001"}

# Parametri connessioni seriale / Serial connection parameters 
BAUDRATE = 9600
thread_stop = 1
"""
- Gateway Class to read the serial data and send them to the online dashboard
- Classe principale per leggere i dati dai sensori collegati in seriale e inviarli al portale online con il protocollo MQTT
"""
class Gateway():
	IDS = 0
	DEVICES = []   # (serial_port, type_device, id)

	def __init__(self, serial_devices : dict):
		""" 
			I dispositivi devono essere passati in input {porta_serial : tipo_di_dispositivo}

			serial_devices : { str_port_serial : Type.Device  } 
		"""
		self.serial_devices = serial_devices

	def run(self):
		""" 
			- Avvia il servizio che colleziona e invia i dati al db/dashboard online
			- Start collecting data and sending them to the online db/dashboard
		"""
		self.init_serial_connection()
		thread_stop = 1
		my_client = init_mqtt_client()
		#connect to the server
		try:
			# loop until the end (the library will manage the connection)
			my_client.loop_forever()
		except (KeyboardInterrupt, SystemExit):
			# close the connection
			my_client.loop_stop()
			thread_stop = 0
			print("Done.")

	def init_serial_connection(self):
		""" init the serial connections on all the devices """
		for dev, dev_type in self.serial_devices.items():
			ser = self.init_serial_connection_subroutine(dev)
			if ser is not None:
				Gateway.DEVICES.append((ser, dev_type, Gateway.IDS))
			Gateway.IDS += 1

	def init_serial_connection_subroutine(self, serial_port : str):
		"""
			Inizializza la connessione seriale verso il dispositivo. 
			serial_port -> la porta seriale sulla quale connettersi

			serial_port : str - The connection port
			Return the connection, if possible, otherwise None
		"""
		try:
			serial_con = serial.Serial(port=serial_port, baudrate=BAUDRATE, 
				parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, 
				bytesize=serial.EIGHTBITS, timeout=0)
		except Exception as e:
			print(e)
			return None 
		return serial_con


"""
- Reader Class for the Raspberry PICO board with Temperature
- Una classe di utilità per leggere temperatura da una Raspberry PICO
"""
class RaspPicoReader():
	
	@classmethod
	def send_MQTT_Message(cls, my_client, dsensor, index_sensor):
		data = {}
		data["temperature_rasp" + str(index_sensor)] = dsensor
		my_client.publish("v1/devices/me/attributes",  json.dumps(ATTRIBUTES), qos=1) #send the attributes to filter out which devices we'll receive 
		my_client.publish("v1/devices/me/telemetry", json.dumps(data), qos=1)
		print("MQTT Message sent from sensor_" + str(index_sensor) + ": " + str(data))

	@classmethod
	def extract_sensor_data(cls, serial : serial.Serial):
		""" 
			Colleziona gli ultimi dati sul seriale, se alcuni, e li ritorna al chiamante

			Collect and return the last data on the serial port.
			serial : the serial connection from which retrieve the data
			return the data (if any) or None 
		"""
		if serial is None:
			return None 
		try:
			if serial.inWaiting() > 0:
				# read a line from the serial
				# legge una riga di dati dalla connessione seriale
				tot_temp = 0.0 
				count = 0.0
				for line in serial:
					count += 1
					tot_temp += float(line)
				# return a mean of the last data, if any
				# ritorna la media delle ultime osservazioni, se alcune
				if count > 0:
					return tot_temp / count   
			return None 
		except (KeyboardInterrupt, SystemExit):
			return None


"""
- Reader Class for the STM32 board with Humidity and Temperature
- Una classe di utilità per leggere umidità e temperatura da una board STM32
"""
class STMReader():
	

	@classmethod
	def send_MQTT_Message(cls, my_client, dsensor, index_sensor):
		data = {}
		data["temperature_stm" + str(index_sensor)] = dsensor[0]
		data["humidity_stm" + str(index_sensor)] = dsensor[1]
		my_client.publish("v1/devices/me/attributes",  json.dumps(ATTRIBUTES), qos=1) #send the attributes to filter out which devices we'll receive 
		my_client.publish("v1/devices/me/telemetry", json.dumps(data), qos=1)
		print("MQTT Message sent from sensor_" + str(index_sensor) + ": " + str(data))

	@classmethod    
	def extract_data_subroutine(cls, line):
		""" 
			- Extract the actual data from the received string from the sensor
			- Estrare i dati in formato testo ricevuti sul seriale
		"""
		if not re.match(reg_match, line):
			return None 

		m = re.findall(reg_extract, line)
		if len(m) == 2:  #ha estratto correttamente entrambi i valori temp e humidity
			return (m[0][1:-1], m[1][1:-1])
		return None 

	@classmethod
	def extract_sensor_data(cls, serial : serial.Serial):
		""" 
			Colleziona gli ultimi dati sul seriale, se alcuni, e li ritorna al chiamante

			Collect and return the last data on the serial port.
			serial : the serial connection from which retrieve the data
			return the data (if any) or None 
		"""
		if serial is None:
			return None 
		try:
			if serial.inWaiting() > 0:
				# read a line from the serial
				# legge una riga di dati dalla connessione seriale
				tot_temp = 0.0
				tot_hum = 0.0
				count = 0.0
				for line in serial:
					extract = extract_data_subroutine(line)
					if extract is not None: 
						count += 1
						tot_temp += float(extract[0])
						tot_hum += float(extract[1])
				# return a mean of the last data, if any
				# ritorna la media delle ultime osservazioni, se alcune
				if count > 0:
					return (tot_temp / count, tot_hum / count)   
			return None 
		except (KeyboardInterrupt, SystemExit):
			return None


#---------------------------------- MQTT and GATEWAY METHODS ---------------- #

def on_connect(my_client, userdata, rc, *extra_params):
	print("MQTT Connected with result code: " + str(rc))
	# subscribe a channel
	my_client.subscribe("v1/devices/me/attributes") #data to thingsboard
	my_client.subscribe("v1/devices/me/telemetry") #data to thingsboard
	t = threading.Thread(target=send_data, args=(my_client,))
	t.deamon = True
	t.start()

def isAlarm(temp):
	return temp >= 29
	
def send_data(my_client):
	while thread_stop: #change the message in order to have some messages for tests.
		for dev in Gateway.DEVICES:
			if dev[1] ==  DeviceType.RaspPICO:
				data = RaspPicoReader.extract_sensor_data(dev[0])
				if data is not None: #error in read
					RaspPicoReader.send_MQTT_Message(my_client, data, dev[2])
			elif dev[1] == DeviceType.STM:
				data = STMReader.extract_sensor_data(dev[0])
				if data is not None: #error in read
					STMReader.send_MQTT_Message(my_client, data, dev[2])
			else:
				print("Type unkwnown")    
		#sleep time -- send data each 2 seconds
		time.sleep(2)

def on_disconnect(client, userdata, rc):
	print("MQTT Disconnected")

def on_message(client, userdata, msg):
	# received a message
	try: 
		message = json.loads(str(msg.payload.decode("utf-8")))
		print("MQTT msg arrived: " + str(message))
		print("MQTT msg topic: " + msg.topic)
	except: #if the json is not correct
		print("MQTT message not formatted")

def init_mqtt_client():
	""" 
		- Inizializza il servizio MQTT per il trasferimento dati 
		- Init the MQTT protocol to share data with the online dashboard
	"""
	my_client = mqtt.Client()
	my_client.on_connect = on_connect
	my_client.on_message = on_message
	my_client.on_disconnect = on_disconnect
	#set token for connection, only token, no username and psw
	my_client.username_pw_set(MQTT_TOKEN)
	#host and port
	my_client.connect(MQTT_HOST, 1883)
	return my_client


if __name__ == "__main__":
	# TODO: Cambiare qui con le porte corrette, e il numero di devices
	device_to_connect = {"/dev/ttyACM0" : DeviceType.RaspPICO, "/dev/ttyACM1" : DeviceType.RaspPICO} 
	gat = Gateway(device_to_connect)   
	gat.run()