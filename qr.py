# import cv2
# from pyzbar.pyzbar import decode
# import os

# if os.name == 'nt':  # Only on Windows
#     import winsound

# # import winsound

# # Beep sound parameters
# def play_beep():
#     frequency = 1000  # Set Frequency To 1000 Hertz
#     duration = 500  # Set Duration To 500 ms (0.5 seconds)
#     winsound.Beep(frequency, duration)

# # Capture webcam
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     print("Error: Could not open camera.")


# while cap.isOpened():
#     success, frame = cap.read()
#     # Flip the image like mirror image
#     frame = cv2.flip(frame, 1)
#     # Detect the barcode
#     detectedBarcode = decode(frame)

#     for barcode in detectedBarcode:
#         # Decode the barcode data
#         barcode_data = barcode.data.decode('utf-8')
#         if barcode_data:
#             print(f"{barcode_data}")
#             cv2.putText(frame, barcode_data, (50, 50), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 255, 255), 2)
#             play_beep()
#             cv2.imwrite("code.png", frame)

#             # Exit the program after detecting a barcode
#             cap.release()
#             cv2.destroyAllWindows()
#             exit()

#     cv2.imshow('scanner', frame)
#     if cv2.waitKey(1) == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()

import cv2
from pyzbar.pyzbar import decode
import os

# Beep sound parameters (only for Windows)
def play_beep():
    if os.name == 'nt':  # Only play beep on Windows
        import winsound
        frequency = 1000  # Set Frequency To 1000 Hertz
        duration = 500    # Set Duration To 500 ms (0.5 seconds)
        winsound.Beep(frequency, duration)
    else:
        # Alternative sound or print message on non-Windows systems
        print("\a")  # ASCII Bell character for simple beep sound

# Capture webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Error: Could not read frame from camera.")
        break

    # Flip the image like a mirror image
    frame = cv2.flip(frame, 1)

    # Detect the barcode
    detectedBarcode = decode(frame)

    for barcode in detectedBarcode:
        # Decode the barcode data
        barcode_data = barcode.data.decode('utf-8')
        if barcode_data:
            print(f"{barcode_data}")
            # Display the barcode data on the frame
            cv2.putText(frame, barcode_data, (50, 50), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 255, 255), 2)

            # Play beep sound
            play_beep()

            # Save the frame containing the barcode as an image
            cv2.imwrite("code.png", frame)

            # Exit the program after detecting a barcode
            cap.release()
            cv2.destroyAllWindows()
            exit()

    # Show the video feed with the scanner window
    cv2.imshow('scanner', frame)

    # Press 'q' to quit the program manually
    if cv2.waitKey(1) == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
