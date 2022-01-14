from machine import Pin, ADC
import utime

# Temperature sensor
sensor_temp = ADC(4)
ADC_FACTOR = 3.3 / 65535

# Led on-board
led = Pin(25, Pin.OUT)

while True:
    read_raw_tmp = sensor_temp.read_u16() * ADC_FACTOR
    temperature = 27 - (read_raw_tmp - 0.706)/ 0.001721
    print(temperature)
    
    if temperature > 23:
        led.value(1)
    else:
        led.value(0)
        
    utime.sleep(1)