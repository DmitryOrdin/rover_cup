import sys
import socket
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSlider, QLabel, QPushButton,
                             QLineEdit, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal


class CommandSender(QThread):
    finished = pyqtSignal()

    def __init__(self, socket, commands_list):
        super().__init__()
        self.socket = socket
        self.commands_list = commands_list

    def run(self):
        for cmd in self.commands_list:
            try:
                self.socket.sendall(cmd.encode('utf-8'))
                time.sleep(0.1)
            except Exception as e:
                print(f"Error sending {cmd}: {e}")
                break
        self.finished.emit()


class RoverControlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.connected = False
        self.pending_commands = []
        self.slider_values = [90, 90, 90, 90, 90]
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Rover Control Panel')
        self.setGeometry(100, 100, 400, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        connection_group = QGroupBox("Connection")
        connection_layout = QHBoxLayout()

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter server IP address")
        self.ip_input.setText("192.168.1.167")

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        connection_layout.addWidget(QLabel("Server IP:"))
        connection_layout.addWidget(self.ip_input)
        connection_layout.addWidget(self.connect_btn)
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)

        self.sliders = []
        self.labels = []
        slider_names = ['Servo 0', 'Servo 1', 'Servo 2', 'Servo 3', 'Servo 4']

        for i, name in enumerate(slider_names):
            slider_group = QGroupBox(name)
            slider_layout = QVBoxLayout()

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(179)
            slider.setValue(90)
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)

            slider.sliderPressed.connect(lambda idx=i: self.on_slider_pressed(idx))
            slider.sliderReleased.connect(lambda idx=i: self.on_slider_released(idx))
            slider.valueChanged.connect(lambda value, idx=i: self.on_slider_value_changed(idx, value))

            label = QLabel(f"Angle: {slider.value()}°")

            slider_layout.addWidget(slider)
            slider_layout.addWidget(label)
            slider_group.setLayout(slider_layout)

            layout.addWidget(slider_group)
            self.sliders.append(slider)
            self.labels.append(label)

        reset_btn = QPushButton("Reset All to 90")
        reset_btn.clicked.connect(self.reset_sliders)
        reset_btn.setStyleSheet("background-color: #FF9800; font-weight: bold;")
        layout.addWidget(reset_btn)

        info_label = QLabel("Command format: 4-digit number [Servo ID(0-4)][Angle(000-179)]")
        info_label.setStyleSheet("color: #2196F3; font-size: 10px;")
        layout.addWidget(info_label)

        info_label2 = QLabel("Commands are sent only when slider is released")
        info_label2.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
        layout.addWidget(info_label2)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.log_text)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_queue)
        self.queue_timer.start(100)

        self.sender_thread = None

    def on_slider_pressed(self, slider_id):
        self.log(f"Servo {slider_id}: slider pressed")

    def on_slider_released(self, slider_id):
        angle = self.sliders[slider_id].value()
        self.log(f"Servo {slider_id}: slider released at {angle}")
        self.send_command(slider_id, angle)

    def on_slider_value_changed(self, slider_id, value):
        self.labels[slider_id].setText(f"Angle: {value}")
        self.slider_values[slider_id] = value

    def send_command(self, servo_id, angle):
        if not self.connected or not self.client_socket:
            self.log("Not connected to server")
            return False

        command = f"{servo_id}{angle:03d}"
        self.pending_commands.append(command)
        self.log(f"Added to queue: {command} (Servo {servo_id} -> {angle})")
        return True

    def process_queue(self):
        if not self.connected or not self.client_socket:
            return

        if (self.sender_thread is None or not self.sender_thread.isRunning()) and self.pending_commands:
            commands_to_send = self.pending_commands.copy()
            self.pending_commands.clear()

            self.log(f"Sending {len(commands_to_send)} command(s) with 100ms delay...")

            self.sender_thread = CommandSender(self.client_socket, commands_to_send)
            self.sender_thread.finished.connect(self.on_commands_sent)
            self.sender_thread.start()

    def on_commands_sent(self):
        self.log("All commands sent successfully")
        self.sender_thread = None

    def reset_sliders(self):
        self.log("Resetting all servos to 90...")
        for i, slider in enumerate(self.sliders):
            slider.setValue(90)
            self.send_command(i, 90)
        self.log("Reset commands added to queue")

    def toggle_connection(self):
        if not self.connected:
            self.connect_to_server()
        else:
            self.disconnect()

    def connect_to_server(self):
        ip = self.ip_input.text().strip()
        if not ip:
            self.log("Please enter IP address")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(3)
            self.client_socket.connect((ip, 4500))
            self.client_socket.settimeout(None)

            self.connected = True
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet("background-color: #F44336;")
            self.ip_input.setEnabled(False)
            self.log(f"Connected to {ip}:4500")

            for i, slider in enumerate(self.sliders):
                self.send_command(i, slider.value())

        except socket.timeout:
            self.log(f"Connection timeout to {ip}:4500")
            self.client_socket = None
        except ConnectionRefusedError:
            self.log(f"Connection refused. Is server running on {ip}:4500?")
            self.client_socket = None
        except Exception as e:
            self.log(f"Connection failed: {e}")
            self.client_socket = None

    def disconnect(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        self.connected = False
        self.pending_commands = []

        if self.sender_thread and self.sender_thread.isRunning():
            self.sender_thread.terminate()
            self.sender_thread = None

        self.connect_btn.setText("Connect")
        self.connect_btn.setStyleSheet("")
        self.ip_input.setEnabled(True)
        self.log("Disconnected from server")

    def log(self, message):
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{time_str}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_status(self):
        status = "Connected" if self.connected else "Disconnected"
        self.setWindowTitle(f"Rover Control - {status}")

    def closeEvent(self, event):
        self.disconnect()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = RoverControlGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
