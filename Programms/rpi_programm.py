import socket
import can
import struct
import time

def create_server(host: str, port: int) -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#создание сервера
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f'Сервер запущен на {host}:{port}')
    connection, addr = server_socket.accept()
    print(f'Подключение от {addr}')
    can0 = can.interface.Bus(channel = 'can0', interface = 'socketcan', fd=True)
    
    while(1):
        data = connection.recv(1024)
        print(f'Получено сообщение: {data}')
        data = bytearray(struct.pack("<i", int(data)))
        msg_to_send = can.Message(arbitration_id=0x065, data = data)
        can0.send(msg_to_send)
        time.sleep(0.001) 
a = str(input("IP "))
create_server(a, 4780)
