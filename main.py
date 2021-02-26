#! /usr/bin/python3

#Importando librerias
import time
import sys
import RPi.GPIO as GPIO
import adafruit_character_lcd.character_lcd as characterlcd
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import busio
import board
import digitalio
from hx711 import HX711
from emulated_hx711 import HX711


"""
Mapa de pines
boton = 4
capacitivo = 18
inductivo = 17
celdaA DT = 22
celdaB SCK = 23
LCD1 = 2
LCD2 = 3

Motor 1 Organicos
IN1M1 = 26
IN2M1 = 20

Motor 2 Inorganicos reciclables
IN3M2 = 19
IN4M2 = 16

Motor 3 Inorganicos NO reciclables 
IN1M3 = 6
IN2M3 = 12
"""
#Seleccionando el modo de visualizacion
#de pines, forma GPIO
GPIO.setmode(GPIO.BCM)

EMULATE_HX711=False
referenceUnit = 1

if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

# Inicializando LCD
lcd_columns = 20
lcd_rows = 4

lcd_rs = digitalio.DigitalInOut(board.D10)
lcd_en = digitalio.DigitalInOut(board.D9)
lcd_d7 = digitalio.DigitalInOut(board.D7)
lcd_d6 = digitalio.DigitalInOut(board.D8)
lcd_d5 = digitalio.DigitalInOut(board.D11)
lcd_d4 = digitalio.DigitalInOut(board.D25)

lcd = characterlcd.Character_LCD_Mono(
    lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows
)

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)
ads.gain = 2/3

#Configurando puerto como entrada
GPIO.setup(17,GPIO.IN)
GPIO.setup(18,GPIO.IN)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Configurando puerto como salida
GPIO.setup(26,GPIO.OUT)
GPIO.setup(20,GPIO.OUT)
GPIO.setup(19,GPIO.OUT)
GPIO.setup(16,GPIO.OUT)
GPIO.setup(6,GPIO.OUT)
GPIO.setup(12,GPIO.OUT)


#Creando un objeto de la clase HX711 y LCD
hx = HX711(22, 23)

hx.set_reading_format("MSB", "MSB")

#Calibrado con 1Kg
hx.set_reference_unit(136) #Modificar para calibrar
hx.set_reference_unit(referenceUnit)

def inicializarSensores():
	hx.reset()
	hx.tare()
	return
	
def menBienvenida():
	lcd.message="Basurero Inteligente\n     Lab Diseno\n Prof. Victor Gomez"
	time.sleep(3)
	lcd.clear()
	lcd.message="   Integrantes\n     Gaby\n     Carlos\n     Sebas"
	time.sleep(3)
	lcd.clear()
	return
def primero():
	lcd.message="1) Favor de poner la\nbasura en la bascula\n  y oprimir el boton"
	
def nuevaBasura():
	#Boton para activar el sistema
	inicio = GPIO.input(4)
	if inicio == False:
		print('Boton pulsado')
		time.sleep(0.3)
		return inicio
	else:
		#print('no pulsado')
		return inicio

def medir():
	#Favor de ponerlo en la balanza
	valido = 0
	peso = max(0,int(hx.get_weight(1))) #Velocidad de balanza
	if 0 <= peso <= 200:
		print('No registrada')
		print(peso)
		lcd.clear()	
		lcd.message="\nMedida no registrada \n  favor de repetir"
		time.sleep(2)
		lcd.clear()
		capa = 0
		indu = 0
		peso = 0
		foto = 0
		valido = 1
		return capa, indu, peso, foto, valido
	else:
		print('Delante de los sensores')
		lcd.clear()
		lcd.message="2) Favor de poner \n  la basura delante \n  de los sensores"
		time.sleep(5)
		lcd.clear()
		lcd.message="\n    Analizando ."	
		time.sleep(2)
		lcd.message="\n    Analizando .."
		time.sleep(1)
		lcd.message="\n    Analizando ..."
		time.sleep(1)
		lcd.clear()
		capa = GPIO.input(18)
		indu = GPIO.input(17)
		foto = chan.value
		valido = 0
		return capa, indu, peso, foto, valido
	
def clasificar(capa, indu, peso, foto):
	print('Estas son las medidas que llegan')	
	print(capa)
	print(indu)
	print(peso)
	print(foto)
	
	#Detecta solo capacitivo	
	if capa == 0 and indu == 1:
		#Fruta, verdura, Envolturas(papel aluminio)
		print("Detecto el capacitivo")
		
		if 20000 <= peso <= 120000:
			print("Organico")
			lcd.message="\n      Organico"
			GPIO.output(26, GPIO.HIGH)
			GPIO.output(20, GPIO.LOW)
			#Abriendo puerta		
			time.sleep(2.0) #2 segundos
			lcd.clear()
			
		elif 300 <= peso <= 10000:
			print("Envoltura")
			lcd.message="\n     Envoltura"
			GPIO.output(6, GPIO.HIGH)
			GPIO.output(12, GPIO.LOW)
			#Abriendo puerta			
			time.sleep(2.0) #2 segundos
			lcd.clear()
			
		else:
			print("No valido")
			lcd.message="\n     No valido"
			time.sleep(2)
			lcd.clear()
		return 1
	
	#Detectan los dos
	elif indu == 0 or capa == 0:
		#Metal, Tetra pack, Latas, Papel aluminio
		print("Detecto el inductivo")
		
		if 1000 <= peso <= 15500:
			print("Tetra pack")
			lcd.message="\n     Tetrapack"
			GPIO.output(19, GPIO.HIGH)
			GPIO.output(16, GPIO.LOW)
			#Abriendo puerta	
			time.sleep(2.0) #2 segundos
			lcd.clear()
			
		elif 15501 <= peso <= 25000:
			print("Latas")
			lcd.message="\n      Latas"
			GPIO.output(19, GPIO.HIGH)
			GPIO.output(16, GPIO.LOW)
			#Abriendo puerta			
			time.sleep(2.0) #2 segundos
			lcd.clear()
			
		else:
			print("No valido")
			lcd.message="\n     No valido"
			time.sleep(2)
			lcd.clear()
		return 2
	
	#Ninguno detecta
	else:
		#Carton y plastico		
		print("Sin detectar")
		#Es una botella
		if foto in range(4000, 15000):
			if peso in range(5000,15500):	
				print("Botella")
				lcd.message="\n     Botella"
				GPIO.output(19, GPIO.HIGH)
				GPIO.output(16, GPIO.LOW)
				#Abriendo puerta			
				time.sleep(2.0) #2 segundos
				lcd.clear()
			else:
				print("No valido")
				lcd.message="\n     No valido"
				time.sleep(2)
				lcd.clear()
				
		elif 300 <= foto <= 1000:
			if peso in range(3000,4999):				
				print("Carton")
				lcd.message="\n     Carton"
				GPIO.output(19, GPIO.HIGH)
				GPIO.output(16, GPIO.LOW)
				#Abriendo puerta			
				time.sleep(2.0) #2 segundos
				lcd.clear()
			else:
				print("No valido")
				lcd.message="\n     No valido"
				time.sleep(2)
				lcd.clear()
		else:
			print("No valido")
			lcd.message="\n     No valido"
			time.sleep(2)
			lcd.clear()
			
		return 3

inicializarSensores()
menBienvenida()
while True:
	try:
		primero()
		inicio = nuevaBasura()
		if inicio == 0:
				print("Proceso")
				capa, indu, peso, foto, valido = medir()
				if valido == 1:
					pass
				
				else:
					clasificar(capa, indu, peso, foto)
					time.sleep(0.5)
		else:
			#No ha apretado el boton		
			GPIO.output(26, GPIO.LOW)
			GPIO.output(20, GPIO.LOW)
			GPIO.output(19, GPIO.LOW)
			GPIO.output(16, GPIO.LOW)
			GPIO.output(6, GPIO.LOW)
			GPIO.output(12, GPIO.LOW)
		time.sleep(0.1)
	except (KeyboardInterrupt, SystemExit):
		lcd.clear()
		cleanAndExit()