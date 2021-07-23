import requests
import asyncio

url = 'https://api.simpletap.com.br'


async def create_client_transaction(volume, drink_price, drink_id, drink_name, client_id, client_cpf, token, sio, reason):
    """
        Função que vou criar as transações no banco de dados,
        Para debitar o dinheiro da conta do cliente
    """
    print('Creating the client transaction...')
    transactionValue = (volume * drink_price) / 100
    data = {
        'type': 'debit',
        'value': transactionValue,
        'volume': volume,
        'drinkId': drink_id,
        'drinkName': drink_name,
        'userId': client_id,
        'userCpf': client_cpf,
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(f'{url}/transactions', json=data, headers=headers)
    responseData = response.json()
    finalBalance = responseData['finalBalance']
    await sio.emit('closedTap', {'volume': volume, 'finalBalance': finalBalance, 'transactionValue': transactionValue, 'reason': reason})
