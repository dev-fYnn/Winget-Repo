# 🛠️ Winget-Repo Setup Guide

Get started with your own custom **Winget-Repo** repository.

---

## ✅ Requirements

- A machine or server with Python support (Tested on Windows)
- Administrator access to both the server and client machines
- Python **3.10 or higher** installed

---

## 📖 Setup Instructions

### 1. 📥 Download and Extract the Repository

- Download the Winget-Repo source code from the official repository.
- Extract the archive to a directory of your choice.

---

### 2. 🐍 Install Python 3.10 or Higher

- Download and install Python from the official website:  
  [https://www.python.org/downloads/](https://www.python.org/downloads/)

---

### 3. 🔌 **Install Packages**   
   Open a Command Prompt (CMD) and run the following commands to install the following packages:
   ```bash
   python -m pip install Flask
   python -m pip install dnspython
   python -m pip install pyyaml
   python -m pip install requests
   python -m pip install cryptography
   ```
   Or just run ```pip install -r requirements.txt``` to install all dependencies.

---

### 4. 🔐 (Recommended) Set Up a Reverse Proxy

To ensure secure HTTPS communication (required by Winget), set up a **reverse proxy** (e.g., Apache or Nginx) in front of the Flask server.

> There are many tutorials available online to help you set up an Apache or Nginx webserver for Python.

---

### ⚠️ Alternative (Not Recommended): Use Flask’s Built-in HTTPS

If you choose not to set up a reverse proxy, you can enable HTTPS in Flask by modifying `main.py` as follows:

```python
if __name__ == '__main__':
    app.run(ssl_context=('SSL/cert.pem', 'SSL/server.pem'))
```

---

### 5. 🛡️ SSL Certificate

You can either:

- Generate a **self-signed SSL certificate** using [OpenSSL](https://www.openssl.org/) or a similar tool  
- **Purchase a valid SSL certificate**

> ⚠️ If using a self-signed certificate, you must install it on **every client** that will connect to the Winget-Repo.

---

### 6. 🌐 Start the Server

Start your web server based on your setup from **Step 4** and connect to your configured address.

🎉 You're ready to go! Enjoy using your private Winget-Repo.

---
