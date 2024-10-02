import socket, sys, cv2, pickle, struct
from threading import Thread
from time import sleep
import pyaudio
import numpy as np

# Global constants
sending, receiving = False, False
HEADERSIZE = 10

# PyAudio configurations
chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 1  # Mono audio
fs = 44100  # Record at 44100 samples per second

class myClass:
    def __init__(self, name="Client", img=None):  # We set default values to avoid issues
        self.threads = []
        self.stop = False
        self.name = name  # Client identifier
        self.img = img  # Placeholder for image (set to None for now)
        self.local_buffer = None
        self.p = pyaudio.PyAudio()

        # PyAudio stream
        self.stream = self.p.open(format=sample_format, channels=channels, rate=fs, 
                                  frames_per_buffer=chunk, input=True, output=True)
        print(f"[DEBUG] Initialized client {self.name}")

    def send_to_client(self, clientsocket):
        cam = cv2.VideoCapture(0)
        cam.set(3, 320)
        cam.set(4, 240)
        img_counter = 0
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        while True:
            ret, frame = cam.read()
            if not ret:
                print("[ERROR] Could not read frame from camera")
                continue
            try:
                result, frame = cv2.imencode('.jpg', frame, encode_param)
            except Exception as e:
                print(f"[ERROR] Encoding frame failed: {e}")
                continue
            data = pickle.dumps(frame, 0)
            size = len(data)
            if self.stop:
                break
            else:
                clientsocket.sendall(bytes(f"{len(data):<{HEADERSIZE}}", 'utf-8') + data)
                img_counter += 1
                sleep(0.5)
        print("Client stopped sending!")
        cam.release()

    def receive_from_client(self, clientsocket):
        print("Receiving...")
        while not self.stop:
            try:
                data = b""
                msg_size = int(clientsocket.recv(HEADERSIZE))
                while len(data) < msg_size:
                    data += clientsocket.recv(4096)
                frame_data = data
                if len(frame_data) == 0:
                    continue
                frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                cv2.imshow(self.name, frame)
                cv2.resizeWindow(self.name, 320, 240)
                cv2.waitKey(1)
            except Exception as e:
                print(f"[ERROR] Exception receiving video: {e}")
                break
        print("Receiving stopped.")
        cv2.destroyAllWindows()

    def fetch_audio(self, audio_socket):
        while not self.stop:
            try:
                print("Fetching audio...")
                data = audio_socket.recv(4096)
                self.stream.write(data)
            except Exception as e:
                print(f"Audio fetch error: {e}")
                continue

    def record_audio(self, audio_socket):
        while not self.stop:
            data = self.stream.read(chunk)
            audio_socket.sendall(data)

    def initiate(self, clientsocket, audio_socket):
        t = Thread(target=self.send_to_client, args=(clientsocket,))
        t2 = Thread(target=self.receive_from_client, args=(clientsocket,))
        
        audio_send_thread = Thread(target=self.record_audio, args=(audio_socket,))
        audio_receive_thread = Thread(target=self.fetch_audio, args=(audio_socket,))
        
        self.stop = False
        while len(self.threads) != 2:
            try:
                c = int(input("Enter 1 to send, 2 to receive: "))
            except ValueError:
                print("Invalid input, please enter 1 or 2.")
                continue
            if c == 1:
                t.start()
                audio_receive_thread.start()
                self.threads.append(t)
            elif c == 2:
                t2.start()
                audio_send_thread.start()
                self.threads.append(t2)

    def end(self):
        self.stop = True
        for t in self.threads:
            t.join()
        self.stream.close()
        self.p.terminate()

# Client configuration
name = "Client 1"  # You can change this for each client
img = None

# Server connection details
IP = "192.168.99.230"  # Server IP address
PORT = 1234  # Audio port

# Establish socket connections
audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
s.connect((IP, 1222))  # Connect for video
audio_socket.connect((IP, PORT))  # Connect for audio

# Initialize the class and start communication
obj = myClass(name, img)  # Name and img are passed properly
obj.initiate(s, audio_socket)

# End communication when done
input("Press Enter to stop...")
obj.end()
s.close()
