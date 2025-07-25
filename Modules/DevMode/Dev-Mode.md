# Winget-Repo Dev Setup Guide

This guide explains how to install and run the Winget-Repo server in **Dev Mode** using the provided `Winget-Repo_Dev.winget` configuration file.

## 🛠️ Installation via `winget configure`

### 1. Open Command Prompt as Administrator

Right-click on **Command Prompt** and choose **"Run as administrator"**.

### 2. Navigate to the Repository Folder

Use the `cd` command to switch to the directory where you downloaded or cloned this repository.

Example:
```cmd
cd C:\Path\To\Downloaded\Repository
```

### 3. Run the Winget Configuration File

Execute the `.winget` file using the following command:
```cmd
winget configure Winget-Repo_Dev.winget
```

This command installs all necessary components as defined in the configuration.

---

## 🚀 Start the Winget-Repo Server

After the configuration is complete, start the server by running:
```cmd
.\start_flask.bat
```

This will launch the Flask server in Dev Mode locally.

---

## 🌐 Access the Winget-Repo Web Interface

Open your web browser and go to:

[https://localhost:5000](https://localhost:5000)

You may see a warning due to the self-signed certificate.

---

## 🔐 Install the Self-Signed Certificate

In order for the Winget client to trust the local Winget-Repo server:

1. Use your browser to export the self-signed certificate from the website (as a `.crt` or `.cer` file).
2. Locate the exported certificate file on your computer.
3. Double-click the certificate file and start the installation wizard.
4. Choose **"Local Machine"** as the store location (you may be prompted for administrator permission).
5. Select **"Place all certificates in the following store"** and browse to:
   - **Trusted Root Certification Authorities**
6. Complete the wizard to install the certificate.

This allows the Winget client to establish a secure connection.

---

## ⚠️ Dev Mode Limitations

- Only **one client** with the name `LOCALHOST` can be created -> Note that you still have to set your DNS ip in the Winget-Repo settings.
- The Dev Mode server is **not accessible from outside** the local machine.
- This mode **is not secure** and **not suitable** for production use.

> **Note:** Dev Mode is strictly for testing and development purposes.  
> **Never use it in a production environment.**

---

📝 For any issues or contributions, feel free to open an issue or pull request.