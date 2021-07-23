# -*- coding: utf-8 -*-

#Bibliotecas do servidor (João)
import asyncio
from aiohttp import web
import socketio
from threading import Lock
import requests

# from client import send_sensor_data (João)
from get_client_and_tap_details import get_client_and_tap_details
from create_client_transaction import create_client_transaction
from create_beer_transaction import create_beer_transaction

#Bibliotecas dos sensores e atuadores (Andrew)
import time                         # Biblioteca temporizadores       
import RPi.GPIO as GPIO             # Biblioteca para usar o RFID
from gpiozero import LED            # Biblioteca para usar saída digital
from mfrc522 import SimpleMFRC522   # Biblioteca para usar o RFID

#Declaração de variáveis globais (Andrew)
global led, timer, channel, tempo_novo, prev, tot, vazao, volume, vol, restante, saldo, abriu

# Declaração do porta de saida acionada válvula (Andrew)
led = LED(27)

# Configuração da biblioteca SimpleMFRC522 RFID(Andrew)
reader = SimpleMFRC522()

# Declação das variáveis utilizadas no sensor (Andrew)
timer = 0.0
tot=0.0
vazao=0.0
volume=0.0
restante = 0.0
saldo = 0
abriu = False
f = 0                        # Frequencia calculada
T = 0                        # Periodo calculado

#Variaveis do temporizador
temp_anterior = 0.0          # Tempo anterior para medida do intervalo
temp_atual = 0.0             # Tempo atual para medida do intervalo
intervalo = 1               # Intervalo para as medidas em ms


# Configuração da entrada para o sensor de fluxo (Andrew)
channel=22                      # Define a porta da entrada                 
GPIO.setmode(GPIO.BCM)          # Define se é a numero de placa ou GPIO
GPIO.setup(channel, GPIO.IN)    # Configura a porta como entrada
GPIO.add_event_detect(channel, GPIO.RISING)  # Insere uma deteccao de eventos na porta


sio = socketio.AsyncServer(
    async_mode='aiohttp', async_handlers=True, cors_allowed_origins='*', ping_interval=500000000)
app = web.Application()
sio.attach(app)

thread = None
thread_lock = Lock()

drink_price = -1
drink_name = ""
drink_id = ""
tap_id = ""
token = ""
actual_sid = 0
card_id = '----'


# Função sensor
###############################################################################################################
async def send_sensor_data():
    #Declaração de variáveis globais (Andrew)
    global led, timer, channel, tempo_novo, prev, tot, vazao, volume, vol, restante, saldo, abriu

    print('Started background task from scratch!')

    ###########################################################################################################
    while True:     #while principal
               
        global card_id
        print('(Re)started background task')

        await sio.sleep(0)

        if actual_sid == '':
            await sio.sleep(0.5)
            print('Zero clients connecteds, breaking the loop.')
            break

        if token == "":
            await sio.sleep(0.5)
            print('Trying to get client information without the token')
            continue

        if card_id == '----':
            print("Aproxime o cartão para fazer a leitura:")
            id, text = reader.read()
            print("O codigo do cartão e: ",id)
            print("O texto gravado no cartao e: ",text)

            card_id = id

        #Envia o card_id para a API e faz a consulta retornando (João)
        client, tap_volume = await get_client_and_tap_details(card_id, tap_id, token, drink_price, sio)
        print('Finished getting the client information!')
        if client == '':
            await sio.sleep(0.5)
            card_id = '----'
            continue
        
        max_volume_for_client_balance = round(client['balance'] / (drink_price/100)) - 0       

        # O volume máximo é o que for menor: o quanto o cliente pode pagar ou o quanto tem no barril (João)
        max_volume = max_volume_for_client_balance if (max_volume_for_client_balance < tap_volume) else tap_volume
        max_volume_from = 'client' if (
            max_volume_for_client_balance < tap_volume) else 'tap'
        reason = ''
              
        
        await sio.sleep(0.0)
        
 ###########################################################################################################       
 
 ###########################################################################################################
        
        temp_anterior = time.time()  # Configura os valores iniciais para o temporizador

        #Verifica se tem volume de saldo
        if (max_volume > 0.0):
            
            print('Torneira aberta! O usuário deve se servir em até 5 segundos agora')

            
            timer = time.time() + 5     # Temporizador para detectar abertura da torneira  
            led.on()                    # Abre a valvula
            

            #Enquanto nao estourar o temporizador executa isso
            while (timer > time.time()):
                
                #Calcula o volume do saldo
                restante  = max_volume-volume

                #Verifica se tem volume disponivel e finaliza caso nao
                if (restante <= 0.0):
                    led.off()
                    if max_volume_from == 'client':
                        print('Acabou o saldo do cliente!')
                        reason = 'client'
                    elif max_volume_from == 'tap':
                        print('Acabou o saldo da torneira!')
                        reason = 'tap'
                    volume =  max_volume 
                    
                    await sio.emit('openTap', {'volume': volume})
                    await sio.sleep(0.5)
                    
                    card_id = '----'
                    #client = ''
                    
                    break
                
##############################################################################################################                
                
                if GPIO.event_detected(channel):    # Incrementa o totalizador a cada pulso
                    tot = tot + 1
                
                temp_atual = time.time()    # Inicia o temporizador

                
                #print("tot", tot)
                #print("temp_atual", temp_atual)
                #print("temp_anterior", temp_anterior)
                #print("intervalo", intervalo)
                #print("temp_atual - temp_anterior", temp_atual - temp_anterior)
                
                if (temp_atual - temp_anterior > intervalo):    #Temporizador executa a cada ciclo
                    temp_anterior = temp_atual
                
                    print("temp_atual - temp_anterior", temp_atual - temp_anterior)

                    print("tot", tot)
                    
                    vazao = 2

                    f = tot/intervalo
                    T = (1/f)*1000
                    
                    #vazao = (f/21)
                    #volume_inst = fluxo/60
                    #volume += volume_inst 
                    
                    #print("Fluxo = ", vazao)
                    #print("Volume = ", volume)
                    #print("Totalizador = ",tot)
                    print("Frequencia = ",f)
                    print("Periodo = ",T)

                    tot = 0 

                
                if ((vazao > 1.0) and (abriu == False)):
                    abriu = True
                   
                if (vazao > 0.0):
                    timer = time.time() + 2   

                if (abriu == True) and (volume < max_volume):
                    volume = round(volume)
                    await sio.emit('openTap', {'volume': volume})
                    await sio.sleep(0.5)    

##############################################################################################################

        led.off()                    
        if (abriu  == True):
            abriu = False
        else:
            card_id = '----'
            client = ''
            await sio.emit('clientDoesNotOpenTheTap')          
            abriu = False
            
            continue    
            
        volume = round(volume)
        print('volume',volume)
        print('max_volume', max_volume)
 ########################################################################################################### 
   

 ###########################################################################################################                           
            
                                 
        await create_client_transaction(
            volume, drink_price, drink_id, drink_name, client['id'], client['cpf'], token, sio, reason)
        print('Done with the client transaction!')
        await create_beer_transaction(
            volume, client['id'], tap_id, drink_id, drink_name, token)
        print('Done with the beer transaction!')
        client = ''
        volume = 0.0
        restante = 0.0
        vazao = 0.0
        tot = 0.0
        print('finished background task, starting it again')
        # <-------------------------------------------------------------------->
        card_id = '----'
    global thread
    print('Finishing background task...')
    thread.cancel()
    thread = None



@sio.event
def connect(sid, environ):
    global actual_sid
    print(f'Tap connected with id: {sid} ')  # sid => session id
    actual_sid = sid
    global thread
    with thread_lock:
        if thread is None:
            thread = sio.start_background_task(send_sensor_data)


@sio.event
def tapInformations(sid, data):
    # Aqui eu vou receber as informações do frontend assim que houver conexão
    print('Data received from tap!')
    print(data)
    global drink_price, tap_id, token, drink_name, drink_id
    drink_price = data['drinkPrice']
    drink_name = data['drinkName']
    drink_id = data['drinkId']
    tap_id = data['tapId']
    token = data['token']


@sio.event
def disconnect(sid):
    print(f'Tap with id: {sid} disconnected!')
    print(f'Last card_id: {card_id}')
    global thread
    print('Finishing background task...')
    thread.cancel()
    thread = None
    global actual_sid
    actual_sid = ''


if __name__ == '__main__':
    web.run_app(app, port=5050)

