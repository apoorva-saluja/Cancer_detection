import speech_recognition as sr
from fpdf import FPDF
from cryptography.fernet import Fernet
from datetime import datetime
import time
from pydub import AudioSegment
from pydub.playback import play
import os

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Generate a passkey for encryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Function to encrypt text
def encrypt_text(plain_text):
    return cipher_suite.encrypt(plain_text.encode()).decode()

# Function to decrypt text
def decrypt_text(encrypted_text):
    return cipher_suite.decrypt(encrypted_text.encode()).decode()

# Function to record and return an audio file path
def record_audio_to_file(filename="temp_audio.wav"):
    with sr.Microphone() as source:
        print("Recording... Speak now.")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)  # Increased phrase_time_limit to 15 seconds
        with open(filename, "wb") as f:
            f.write(audio.get_wav_data())
        return filename

# Function to transcribe audio from file
def transcribe_audio(filename):
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
        try:
            message = recognizer.recognize_google(audio)
            print(f"Transcription: {message}")
        except sr.UnknownValueError:
            message = "Could not understand audio"
            print(message)
        except sr.RequestError as e:
            message = f"Could not request results from Google Speech Recognition service; {e}"
            print(message)
    
    return message

# Function to play the recorded audio file using pydub
def play_audio(filename):
    audio = AudioSegment.from_wav(filename)
    play(audio)

# Function to save encrypted data to a PDF
def save_encrypted_to_pdf(transcriptions, filename="encrypted_messages.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Encrypted Audio Messages", ln=True, align="C")

    pdf.set_font("Arial", size=12)

    # Add the encryption key to the PDF
    pdf.ln(10)
    pdf.multi_cell(200, 10, f"Encryption Key: {key.decode()}")

    for i, (timestamp, _, encrypted_message) in enumerate(transcriptions, 1):
        pdf.ln(10)
        pdf.multi_cell(200, 10, f"Message {i} - Recorded on: {timestamp}\n\nEncrypted Message:\n{encrypted_message}")
    
    # Save the PDF
    pdf.output(filename)
    print(f"Encrypted messages saved as {filename}")

# Function to save decrypted data to a PDF
def save_decrypted_to_pdf(transcriptions, filename="decrypted_messages.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Decrypted Audio Messages", ln=True, align="C")

    pdf.set_font("Arial", size=12)

    for i, (timestamp, message, _) in enumerate(transcriptions, 1):
        pdf.ln(10)
        pdf.multi_cell(200, 10, f"Message {i} - Recorded on: {timestamp}\n\nDecrypted Message:\n{message}")
    
    # Save the PDF
    pdf.output(filename)
    print(f"Decrypted messages saved as {filename}")

# Function to handle recording and editing of audio messages
def record_audio_messages():
    transcriptions = []
    while True:
        # Step 1: Record the audio and save it to a temporary file
        audio_file = record_audio_to_file()

        # Step 2: Allow the user to replay the audio
        print("Playing back the recorded audio...")
        play_audio(audio_file)

        # Step 3: Transcribe the audio and show the transcription
        transcription = transcribe_audio(audio_file)

        # Step 4: Ask the user whether to keep, re-record, or discard
        while True:
            choice = input(f"Transcription: '{transcription}'\nDo you want to Keep (K), Re-record (R), or Discard (D) the message? ").strip().lower()
            if choice == 'k':
                if transcription != "Could not understand audio":
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current date and time
                    encrypted_message = encrypt_text(transcription)
                    transcriptions.append((timestamp, transcription, encrypted_message))
                break
            elif choice == 'r':
                # Re-record the message
                print("Re-recording the message...")
                audio_file = record_audio_to_file()
                play_audio(audio_file)
                transcription = transcribe_audio(audio_file)
            elif choice == 'd':
                print("Discarding the message.")
                break
            else:
                print("Invalid choice. Please enter 'K' to keep, 'R' to re-record, or 'D' to discard.")

        # Step 5: Ask if the user wants to record another message
        time.sleep(2)  # Add a delay before asking again
        another = input("Do you want to record another message? (yes/no): ").strip().lower()
        if another != 'yes':
            break
    
    # Save the recorded messages to two separate PDFs
    if transcriptions:
        save_encrypted_to_pdf(transcriptions)
        save_decrypted_to_pdf(transcriptions)
    else:
        print("No valid messages were recorded.")

if __name__ == "__main__":
    record_audio_messages()
