import socket
import serial
import threading
import time
import queue


a = str(input("IP"))

HOST = a  # IP-адрес сервера
PORT = 4780 # Порт сервера
rover_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
rover_client.connect((HOST, PORT))
msg = queue.Queue()
port = "COM4"
baud_rate = 9600
ser = serial.Serial(port, baud_rate, timeout=1)
def get_angles():
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            msg.put(line)
def send_angle():
    while True:
        message = msg.get()
        rover_client.sendall(message.encode('utf-8'))
        print(f"Отправлено: {message}")
threading.Thread(target=get_angles(), args=(q,)).start()
threading.Thread(target=send_angle(), args=(q,)).start()

# Сокет автоматически закроется благодаря 'with'
