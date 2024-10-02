import socket
import videosocket
import io
import cv2  # Import OpenCV to handle PiP
from videofeed import VideoFeed
from PIL import Image  # Import PIL for image handling
import numpy as np  # Import NumPy
import sys

class Client:
    def __init__(self, ip_addr="172.17.211.70"):  # Updated IP
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((ip_addr, 6000))
        self.vsock = videosocket.videosocket(self.client_socket)
        self.videofeed = VideoFeed(1, "client", 1)
        self.data = io.BytesIO()

    def connect(self):
        while True:
            # Capture local frame from client camera (your PiP view)
            local_frame = self.videofeed.get_frame()

            # Send local frame to the server
            if local_frame:
                self.vsock.vsend(local_frame)

            # Receive the remote frame from the server
            remote_frame = self.vsock.vreceive()

            if remote_frame is None:
                print("Error: No frame received from server")
                break

            # Display the PiP view (local video overlaid on remote video)
            self.display_pip(remote_frame)

    def display_pip(self, remote_frame_bytes):
        # Convert the received remote frame bytes to an image
        pil_remote_image = Image.open(io.BytesIO(remote_frame_bytes))  # Make sure to import PIL's Image module
        remote_frame = cv2.cvtColor(np.array(pil_remote_image), cv2.COLOR_RGB2BGR)

        # Capture local video frame (for PiP display)
        ret, local_frame = self.videofeed.cam.read()

        if ret:
            # Resize local frame for PiP
            pip_frame = cv2.resize(local_frame, (160, 120))  # Adjust PiP size here

            # Overlay PiP in the bottom-right corner of the remote frame
            x_offset = remote_frame.shape[1] - pip_frame.shape[1] - 10  # 10px from right
            y_offset = remote_frame.shape[0] - pip_frame.shape[0] - 10  # 10px from bottom

            # Overlay local frame (PiP) onto the remote frame
            remote_frame[y_offset:y_offset+pip_frame.shape[0], x_offset:x_offset+pip_frame.shape[1]] = pip_frame

        # Display the combined (PiP) frame
        cv2.imshow("Video with PiP", remote_frame)
        cv2.waitKey(1)

if __name__ == "__main__":
    ip_addr = "172.17.211.70"  # Updated IP
    print("Connecting to " + ip_addr + "....")
    client = Client(ip_addr)
    client.connect()
