import speech_recognition as sr
import pyttsx3
from openai import OpenAI
import serial
import time
import cv2
import time

# Initialize the recognizer
r = sr.Recognizer()
ser = serial.Serial('COM3', 9600)
time.sleep(2)

# Initialize pyttsx3 TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 250)  # Speed percent
engine.setProperty('volume', 0.9)  # Volume
def detect_face():
  # Initialize the webcam
  cap = cv2.VideoCapture(0)
  face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

  ret, frame = cap.read()
  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  faces = face_cascade.detectMultiScale(gray, 1.1, 4)
  cap.release()

  return len(faces) > 0

def send_command_to_arduino(command):
  ser.write((str(command) + '\n').encode())

# Function to recognize speech
def recognize_speech_from_mic(recognizer, microphone):
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        response["error"] = "Unable to recognize speech"

    return response

# Initialize microphone
mic = sr.Microphone()
client = OpenAI()

while True:
    print("Please say something...")
    speech_to_text = recognize_speech_from_mic(r, mic)

    if speech_to_text["transcription"]:
        user_said = speech_to_text["transcription"].lower()
        print("You said: " + user_said)

        if "quit" in user_said:
            print("Exiting...")
            break

        face_present = detect_face()
        if face_present:
            print("Face detected.")
            send_command_to_arduino('2')
        else:
            print("No face detected.")
            send_command_to_arduino('0')

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "If the user says a sentence with the word deal in it return 1, else return 0."},
                {"role": "user", "content": user_said}
            ]
        )
        response_message = completion.choices[0].message.content
        print(response_message)
        engine.say(response_message)
        send_command_to_arduino(response_message)
        engine.runAndWait()
    else:
        print("Sorry, I didn't catch that.")  
