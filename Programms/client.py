import socket


a = str(input("IP"))


HOST = a  # IP-адрес сервера
PORT = 4780 # Порт сервера

rover_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

rover_client.connect((HOST, PORT))

while(1):

    message = (str(input()))
    rover_client.sendall(message.encode('utf-8'))
    print(f"Отправлено: {message}")

# Сокет автоматически закроется благодаря 'with'
