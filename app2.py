from flask import Flask, request, render_template, send_file, redirect, url_for
from cryptography.fernet import Fernet
import os
import pyqrcode
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Fernet encryption key (replace this with your generated key)
key = b'39va-Wk-H6KOzXvj2XpFneIA-k6aox3uho35jKUghtM='
cipher = Fernet(key)

@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file upload and encryption
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Encrypt the uploaded file
        with open(filepath, 'rb') as f:
            data = f.read()
        encrypted_data = cipher.encrypt(data)

        # Save the encrypted file
        enc_filename = filename + '.enc'
        enc_filepath = os.path.join(app.config['UPLOAD_FOLDER'], enc_filename)
        with open(enc_filepath, 'wb') as f:
            f.write(encrypted_data)

        # Generate QR code with the link to access the decryption page (not the encrypted file directly)
        qr_code_url = url_for('decrypt_file', filename=enc_filename, _external=True)
        qr_code = pyqrcode.create(qr_code_url)
        qr_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'qrcode.png')
        qr_code.png(qr_filepath, scale=5)

        return f'QR code generated. Scan to decrypt your ID. <img src="/static/qrcode.png">'

# Route to decrypt and download the file
@app.route('/decrypt/<filename>', methods=['GET', 'POST'])
def decrypt_file(filename):
    if request.method == 'POST':
        password = request.form['password']
        if password == '1234':  # Replace with your password logic
            enc_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            dec_filepath = enc_filepath[:-4]  # Remove ".enc" extension

            # Decrypt the file
            with open(enc_filepath, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = cipher.decrypt(encrypted_data)

            # Save decrypted file as an image
            with open(dec_filepath, 'wb') as f:
                f.write(decrypted_data)

            # Serve decrypted image file for download
            return send_file(dec_filepath, as_attachment=True)

        return 'Incorrect password. Try again.'

    return '''
        <form method="POST">
            Enter password to decrypt the file: 
            <input type="password" name="password">
            <input type="submit" value="Decrypt">
        </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)
