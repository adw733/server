# # Arquivo que vai rodar no Raspberry PI do TAP;
# import socketio
# import uuid
import asyncio

# sio = socketio.Client()


def send_sensor_data(sio):
    print('started background task')
    while True:
        # card_id = str(uuid.uuid4())
        # time.sleep(0.5)
        card_id = input('Digite o id do cartão: ')
        sio.emit('card_on', {'card_id': card_id})
        sio.sleep(3)
        volume = 1
        while volume < 200:
            sio.emit('tap_open', {'volume': volume})
            time.sleep(2)
            volume += 5
        sio.emit('tap_close', {'volume': volume})


# @sio.event
# def connect():
#     print('connection established')
#     sio.start_background_task(send_sensor_data)


# @sio.event
# def disconnect():
#     print('disconnected from server')


# @sio.event
# def tapInformations(sid, data):
#     print(data)


# sio.connect('http://localhost:5050')
# sio.wait()
