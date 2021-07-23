import requests
import asyncio

url = 'https://api.simpletap.com.br'


async def create_beer_transaction(volume, client_id, tap_id, drink_id, drink_name, token):
    """
        Função que vou criar as transações no banco de dados,
        Para diminuir o volume do barril
    """
    print('Creating the beer transaction...')
    data = {
        'type': 'debit',
        'volume': volume,
        'clientId': client_id,
        'tapId': tap_id,
        'drinkId': drink_id,
        'drinkName': drink_name
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    print(f'volume: {volume}')
    response = requests.post(
        f'{url}/beertransactions', json=data, headers=headers)
    responseData = response.json()
    print(responseData)
