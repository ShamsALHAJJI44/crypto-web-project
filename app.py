from flask import Flask, render_template, request, send_file
import os, base64, hashlib
from Crypto.Cipher import AES
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def pad_key(key):
    return key.ljust(16)[:16].encode("utf-8")

def encrypt_aes(key, data):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode("utf-8"))
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode("utf-8")

def decrypt_aes(key, enc_data_b64):
    try:
        enc_data = base64.b64decode(enc_data_b64)
        nonce, tag, ciphertext = enc_data[:16], enc_data[16:32], enc_data[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode("utf-8")
    except:
        return "Şifre çözme hatası!"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/text-aes", methods=["GET", "POST"])
def text_aes():
    result = ""
    if request.method == "POST":
        text = request.form.get("text", "")
        key_input = request.form.get("key", "")
        key = pad_key(key_input)
        action = request.form.get("action")
        if action == "encrypt":
            result = encrypt_aes(key, text)
        elif action == "decrypt":
            result = decrypt_aes(key, text)
    return render_template("text_aes.html", result=result)

@app.route("/sha256", methods=["GET", "POST"])
def sha256():
    result = ""
    if request.method == "POST":
        if request.form.get("action") == "hash_text":
            text = request.form.get("text", "")
            result = hashlib.sha256(text.encode()).hexdigest()
        elif request.form.get("action") == "hash_file":
            file = request.files.get("file")
            if file:
                path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
                file.save(path)
                with open(path, "rb") as f:
                    hash = hashlib.sha256()
                    while chunk := f.read(4096):
                        hash.update(chunk)
                    result = hash.hexdigest()
            else:
                result = "Dosya yok!"
    return render_template("sha256.html", result=result)

@app.route("/file-crypto", methods=["GET", "POST"])
def file_crypto():
    result = ""
    download_link = ""
    if request.method == "POST":
        action = request.form.get("action")
        key_input = request.form.get("key", "")
        key = pad_key(key_input)
        uploaded_file = request.files.get("file")
        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            uploaded_file.save(file_path)

            with open(file_path, "rb") as f:
                data = f.read()

            if action == "encrypt":
                cipher = AES.new(key, AES.MODE_EAX)
                ciphertext, tag = cipher.encrypt_and_digest(data)
                encrypted = cipher.nonce + tag + ciphertext
                out_path = os.path.join(app.config["UPLOAD_FOLDER"], "encrypted_" + filename)
                with open(out_path, "wb") as out:
                    out.write(encrypted)
                result = "Şifreleme başarılı"
                download_link = "/download/encrypted_" + filename

            elif action == "decrypt":
                try:
                    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
                    cipher = AES.new(key, AES.MODE_EAX, nonce)
                    decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                    out_path = os.path.join(app.config["UPLOAD_FOLDER"], "decrypted_" + filename)
                    with open(out_path, "wb") as out:
                        out.write(decrypted)
                    result = "Çözme başarılı"
                    download_link = "/download/decrypted_" + filename
                except:
                    result = "Şifre çözme hatası"
        else:
            result = "Dosya seçilmedi!"
    return render_template("file_crypto.html", result=result, download_link=download_link)

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(app.config["UPLOAD_FOLDER"], filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)