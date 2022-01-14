from machine import Pin, ADC
import utime

# internal led - per controllare che funzioni
led_int = Pin(25, Pin.OUT)
# external led 
led_ext = Pin(15, Pin.OUT)

# temperature
temp_i = ADC(4)
ADC_FACTOR = 3.3/65535

# threshold
threshold = 22

while True:
    # read temperature
    raw_tmp = temp_i.read_u16() * ADC_FACTOR
    temperature = 27 - (raw_tmp - 0.706) / 0.001721
    
    if  temperature > threshold:
        led_ext.toggle()
        led_int.value(0)
    else:
        led_int.toggle()
        led_ext.value(0)
        
    print(temperature)
    utime.sleep(0.5)