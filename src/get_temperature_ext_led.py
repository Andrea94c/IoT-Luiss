# Codice per raspberry Pico con sensore di temperature onboard e led esterno rosso
import machine
import utime

from machine import ADC
sensor_temp = ADC(4) 
conversion_factor = 3.3 / (65535) 
led_external = machine.Pin(15, machine.Pin.OUT)
led_onboard = machine.Pin(25, machine.Pin.OUT)


while True:
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
       
    if temperature > 22:
        led_external.toggle()
        led_onboard.value(0)
    else:
        led_external.value(0)
        led_onboard.toggle()
    
    print (temperature)
    utime.sleep(0.5)
