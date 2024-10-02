import cv2

cam = cv2.VideoCapture(0)
if not cam.isOpened():
    print("Error: Unable to open camera")
else:
    while True:
        ret_val, img = cam.read()
        if not ret_val:
            print("Error: Can't grab frame")
            break
        cv2.imshow('my webcam', img)
        if cv2.waitKey(1) == 27:  # Press 'Esc' to exit
            break
cam.release()
cv2.destroyAllWindows()
