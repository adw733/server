import requests
import asyncio

url = 'https://api.simpletap.com.br'


async def get_client_and_tap_details(card_id, tap_id, token, drink_price, sio):
    print('Getting client informations..')
    response = requests.get(f'{url}/clients/cards/{card_id}/{tap_id}', headers={
        'Authorization': f'Bearer {token}'
    })
    responseData = response.json()
    if response.status_code != 200:
        if responseData['message'] == 'This card does not belong to this pub!':
            await sio.emit('cardFromOtherPub')
            print('Cartão não pertence ao pub!')
        if responseData['message'] == "This card isn't registered":
            await sio.emit('cardDoesNotExists')
        return '', 0
    elif response.status_code == 200:
        client = {
            'id': responseData['client']['id'],
            'name': responseData['client']['name'],
            'balance': responseData['client']['balance'],
            'cpf': responseData['client']['cpf'],
        }
        tap_volume = responseData['volume']
        if tap_volume < 10:
            await sio.emit('tapWithoutVolume')
            print('Torneira com pouco volume!')
            return '', 0

        max_volume_for_client_balance = round(
            client['balance'] / (drink_price/100)) - 10

        if max_volume_for_client_balance <= 5:
            await sio.emit('clientWithoutBalance', {'balance': client['balance']})
            print('Cliente com pouco saldo!')
            return '', 0
        await sio.emit('cardIn', {'cardId': card_id, 'client': client})
        return client, tap_volume
