import cv2 as cv

camera = cv.VideoCapture(0)
rodando = True

while rodando:
    status, frame = camera.read()

    if not status or frame is None or cv.waitKey(1) & 0xFF == ord('q'):
        rodando = False
        continue

    cv.imshow("Camera", frame)

camera.release()
cv.destroyAllWindows()
