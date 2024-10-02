import cv2
import numpy as np  # Use numpy for array manipulations
import io
from PIL import Image

class VideoFeed:

    def __init__(self, mode=1, name="w1", capture=1):
        print(name)
        self.camera_index = 0
        self.name = name
        if capture == 1:
            # Use DirectShow backend to avoid MSMF issues on Windows
            self.cam = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cam.isOpened():
                print(f"Error: Unable to open camera index {self.camera_index}")
                exit(1)

    def get_frame(self):
        ret_val, img = self.cam.read()
        if not ret_val:
            print(f"Error: Can't grab frame from camera index {self.camera_index}")
            return None  # If no frame is captured, return None
        c = cv2.waitKey(1)
        if c == ord("n"):  # Press 'n' to switch to the next camera
            self.camera_index += 1
            self.cam = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cam.isOpened():
                print(f"Error: Unable to open camera index {self.camera_index}")
                self.camera_index = 0
                self.cam = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

        # Convert the captured image to bytes for sending
        cv2_im = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_im = Image.fromarray(cv2_im)
        b = io.BytesIO()
        pil_im.save(b, 'jpeg')
        im_bytes = b.getvalue()
        return im_bytes

    def set_frame(self, frame_bytes):
        pil_bytes = io.BytesIO(frame_bytes)
        pil_image = Image.open(pil_bytes)
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        cv2.imshow(self.name, cv_image)
        cv2.waitKey(1)

    def get_local_frame(self):
        """ Captures the local frame for PiP """
        ret_val, img = self.cam.read()
        if not ret_val:
            print("Error: Can't grab local frame")
            return None
        return img  # Returns the raw OpenCV image
