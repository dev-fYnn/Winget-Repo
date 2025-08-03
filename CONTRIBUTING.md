# Contributing to Winget-Repo

Thank you for your interest in contributing to Winget-Repo!  
This guide will help you set up your development environment and contribute effectively.

---

## 🧰 Development Environment Setup

To run Winget-Repo in Dev Mode, follow these steps:

### 1. Fork and Clone the Repository

```bash
git clone https://github.com/dev-fYnn/winget-repo.git
cd winget-repo
```

### 2. Open Command Prompt as Administrator

Right-click on Command Prompt and select **"Run as administrator"**.

### 3. Navigate to the Repository Folder

```bash
cd C:\Path\To\Cloned\Repository
```

### 4. Run the Winget Configuration located in the .github folder

```bash
winget configure Winget-Repo_Dev.winget
```

This will install all required components using the provided configuration file.

---

## 🚀 Running the Server

Start the Flask server in Dev Mode by running:

```bash
.\start_flask.bat
```

Visit the local web interface at:  
[https://localhost:5000](https://localhost:5000)

> You may receive a browser warning due to a self-signed certificate.

---

## 🔐 Trusting the Local Certificate

1. Export the certificate from your browser as `.cer` or `.crt`.
2. Run the file and choose **"Local Machine"**.
3. Install it into the **Trusted Root Certification Authorities** store.

This ensures the Winget client can connect securely.

---

## ⚠️ Dev Mode Limitations

- Only one client named `LOCALHOST` can be created.
- Dev Mode is limited to your local machine.
- **Not suitable for production.** Intended only for testing and development.

---

## ✅ How to Contribute

1. Create a new branch:
   ```bash
   git checkout -b your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git commit -m "Add feature/fix description"
   ```

3. Push your branch:
   ```bash
   git push origin your-feature-name
   ```

4. Open a Pull Request against the main branch of this repository.

---

## 📝 Issues and Support

If you find bugs, have questions, or want to suggest improvements, feel free to:

- Open an [Issue](https://github.com/dev-fYnn/Winget-Repo/issues)
- Submit a [Pull Request](https://github.com/dev-fYnn/Winget-Repo/pulls)

Thanks again for contributing!
