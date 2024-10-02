from flask import Flask, request, jsonify, send_file, render_template
from fpdf import FPDF
from cryptography.fernet import Fernet
from datetime import datetime
import os
from pydub import AudioSegment
import speech_recognition as sr

# Initialize the Flask app
app = Flask(__name__)

# Explicitly set the path to FFmpeg (update this path as per your setup)
AudioSegment.converter = r"C:\Users\apoor\Downloads\ffmpeg-2024-09-26-git-f43916e217-essentials_build\ffmpeg-2024-09-26-git-f43916e217-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\Users\apoor\Downloads\ffmpeg-2024-09-26-git-f43916e217-essentials_build\ffmpeg-2024-09-26-git-f43916e217-essentials_build\bin\ffprobe.exe"

# Generate a passkey for encryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Placeholder for storing transcriptions
transcriptions = []

# Route to serve the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Function to encrypt text
def encrypt_text(plain_text):
    return cipher_suite.encrypt(plain_text.encode()).decode()

# Function to decrypt text
def decrypt_text(encrypted_text):
    return cipher_suite.decrypt(encrypted_text.encode()).decode()

# Function to save encrypted data to a PDF
def save_encrypted_to_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Encrypted Audio Messages", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.multi_cell(200, 10, f"Encryption Key: {key.decode()}")

    for i, (timestamp, _, encrypted_message) in enumerate(transcriptions, 1):
        pdf.ln(10)
        pdf.multi_cell(200, 10, f"Message {i} - Recorded on: {timestamp}\n\nEncrypted Message:\n{encrypted_message}")

    pdf.output("encrypted_messages.pdf")

# Function to save decrypted data to a PDF
def save_decrypted_to_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Decrypted Audio Messages", ln=True, align="C")

    pdf.set_font("Arial", size=12)

    for i, (timestamp, message, _) in enumerate(transcriptions, 1):
        pdf.ln(10)
        pdf.multi_cell(200, 10, f"Message {i} - Recorded on: {timestamp}\n\nDecrypted Message:\n{message}")

    pdf.output("decrypted_messages.pdf")

# Endpoint to process audio
@app.route('/process_audio', methods=['POST'])
def process_audio():
    action = request.form.get('action')
    audio_file = request.files['audio']

    # Log the action and the incoming audio file
    print(f"Received action: {action}")
    print(f"Received audio file: {audio_file.filename}")

    # Save the audio file locally
    audio_path = 'temp_audio.wav'
    audio_file.save(audio_path)

    # Convert audio to WAV format using pydub (ensure it is a valid PCM WAV)
    sound = AudioSegment.from_file(audio_path)
    sound.export(audio_path, format="wav")  # Re-export as WAV (overwrites the original)

    # Now process the converted WAV audio with speech recognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
        try:
            transcription = recognizer.recognize_google(audio)
            print(f"Transcription: {transcription}")
        except sr.UnknownValueError:
            transcription = "Could not understand audio"
            print("Could not understand audio")
        except sr.RequestError as e:
            transcription = "Error in transcription"
            print(f"Transcription error: {e}")

    if action == 'keep':
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        encrypted_message = encrypt_text(transcription)
        transcriptions.append((timestamp, transcription, encrypted_message))

        # Save the encrypted and decrypted PDFs
        save_encrypted_to_pdf()
        save_decrypted_to_pdf()

        # Delete the temporary audio file after processing
        if os.path.exists(audio_path):
            os.remove(audio_path)

    return jsonify({'status': 'success'})

# Endpoint to download encrypted PDF
@app.route('/download/encrypted', methods=['GET'])
def download_encrypted():
    return send_file("encrypted_messages.pdf", as_attachment=True)

# Endpoint to download decrypted PDF
@app.route('/download/decrypted', methods=['GET'])
def download_decrypted():
    return send_file("decrypted_messages.pdf", as_attachment=True)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
