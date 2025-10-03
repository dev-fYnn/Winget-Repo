# Winget-Repo Client

---

## 📖 Overview
**Winget-Repo Client** is an open-source wrapper for the Windows Package Manager (Winget).  
It enables seamless use of **Winget-Repo** and **Winget-Repo Cloud**, providing full functionality for installing and upgrading software directly from your private or cloud-based repository.  

With the client, you can easily connect your Windows devices to **Winget-Repo** and benefit from centralized package management without complex setup.  

---

## 🌟 Features

- 🖱️ **One-Click Installation & Updates:**  Install or update available applications directly from your Winget-Repo or Winget-Repo Cloud via a modern, intuitive interface.

- 🌐 **Automatic Program Listing:** The client fetches available software packages dynamically via REST API from your Winget-Repo server.

- 📦 **Centralized Package Management:** View all applications provided by your repository in one place – no need to search manually.

- 🔄 **Update Management:** See which applications are outdated and update them with a single click.

- ⚡ **Seamless Integration with Winget-Repo:** Works out-of-the-box with both self-hosted Winget-Repo and Winget-Repo Cloud.

- 🔐 **Secure Access:** Supports token-based authentication for connecting clients to your repository.

- 🖥️ **Lightweight Client:** Minimal dependencies, fast setup, and a native look & feel on Windows.

---

## 🛠️ Installation

### Prerequisites
- Windows 10 or later  
- [Winget](https://learn.microsoft.com/windows/package-manager/winget/) installed  
- Access to a **Winget-Repo** server or **Winget-Repo Cloud** account  

### Install Client
Download the latest version from the [Releases page](https://github.com/dev-fYnn/Winget-Repo-Client/releases).  

---

## ⚙️ Configuration

1. **Connect winget to your repository**  
   Connect your client either to **Winget-Repo Cloud** or a **self-hosted Winget-Repo** instance:  
   - [Cloud Setup Guide](https://cloud.winget-repo.io/docs/Client-Connect)  
   - [Self-Hosted Setup Guide](https://github.com/dev-fYnn/Winget-Repo/blob/master/Docs/Connection.md)  

2. **Download Client Configuration**  
   In the **Winget-Repo Dashboard**, navigate to the *Clients* section and download the dedicated `config.ini` file for your device.  

3. **Import Configuration**  
   Open the **Winget-Repo Client**, go to the **Settings tab**, and import the downloaded `config.ini`.

---

## 🤝 Contributing

Contributions are welcome! 🎉  

1. Fork the repository  
2. Create your feature branch (`git checkout -b feature/my-new-feature`)  
3. Commit your changes (`git commit -m 'Add new feature'`)  
4. Push to the branch (`git push origin feature/my-new-feature`)  
5. Open a Pull Request  

Please also check our [contribution guidelines](https://github.com/dev-fYnn/Winget-Repo-Client/blob/master/CONTRIBUTING.md) before submitting PRs.  

---

And if you enjoy using **Winget-Repo Client**, please ⭐ the repo – it helps a lot! 🙏  
