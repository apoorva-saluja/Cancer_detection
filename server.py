import socket
import videosocket
import cv2
from videofeed import VideoFeed
import numpy as np
import io
from PIL import Image
import sys
from threading import Thread

class Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("", 6000))  # No need to change IP on server side as it binds to all interfaces
        self.server_socket.listen(5)
        self.videofeed = VideoFeed(1, "server", 1)
        self.call_active = True  # Flag to control call termination
        print("TCPServer Waiting for client on port 6000")

    def start(self):
        # Start a thread to listen for Enter key to end the call
        key_thread = Thread(target=self.check_for_end_call)
        key_thread.start()

        client_socket, address = self.server_socket.accept()
        print("I got a connection from ", address)
        vsock = videosocket.videosocket(client_socket)

        while self.call_active:
            try:
                # Receive the remote frame from the client
                remote_frame_bytes = vsock.vreceive()
                if remote_frame_bytes is None:
                    print("Error: No frame received from client")
                    break

                # Convert received frame to image for display
                pil_remote_image = Image.open(io.BytesIO(remote_frame_bytes))
                remote_frame = cv2.cvtColor(np.array(pil_remote_image), cv2.COLOR_RGB2BGR)

                # Capture local frame for PiP
                local_frame = self.videofeed.get_local_frame()

                if local_frame is not None:
                    # Resize local frame for PiP
                    pip_frame = cv2.resize(local_frame, (160, 120))  # Small frame size for PiP

                    # Overlay the local frame in the bottom-right corner of the remote frame
                    x_offset = remote_frame.shape[1] - pip_frame.shape[1] - 10  # 10px from right
                    y_offset = remote_frame.shape[0] - pip_frame.shape[0] - 10  # 10px from bottom
                    remote_frame[y_offset:y_offset+pip_frame.shape[0], x_offset:x_offset+pip_frame.shape[1]] = pip_frame

                # Display the PiP view (remote + local frame)
                cv2.imshow("Server PiP View", remote_frame)

                # Check if 'q' is pressed to end the call
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("End call requested")
                    break

                # Send the local frame back to the client
                local_frame_bytes = self.videofeed.get_frame()
                if local_frame_bytes:
                    vsock.vsend(local_frame_bytes)
                else:
                    print("Error: No frame captured to send")
                    break

            except Exception as e:
                print(f"Error occurred: {e}")
                break

        self.end_call(client_socket)

    def end_call(self, client_socket):
        print("Closing connection and cleaning up...")
        self.call_active = False
        client_socket.close()  # Close the client connection
        cv2.destroyAllWindows()  # Close OpenCV windows

    def check_for_end_call(self):
        input("Press Enter to end the call...\n")  # Wait for Enter key press
        self.call_active = False  # Set the flag to False to end the call

if __name__ == "__main__":
    server = Server()
    server.start()
