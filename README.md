
# Winget-Repo 📦

Winget-Repo is a private repository for the Windows Package Manager (Winget), designed to provide software and updates within local networks without internet access. It allows centralized management and efficient installation and updating of software on multiple Windows clients.

# 🌟 Current Features

- **Easy-to-use Web Interface** for managing packages and package versions 🌐
- **Search, List, Show, Install, and Upgrade Packages** via Winget 🔍📦
- **Cross-platform**: The server runs on all environments that support Python 🖥️💻
- **Client Overview**: Track and manage your clients and control who is accessing Winget-Repo 🖥️👀
- **Permission Management**: Control access and user rights 🔐
- **Terms of Service**: Request the agreement of your Terms of Service 📑

# 🚀 Upcoming Features

- **Library for Click and Deploy Software**: Simplified deployment of software with just a click 🖱️📲
- **Support for Nested Installers** 🛠️🔄
- **Winget-Client**: Use Winget easily on your client 🖥️💿
- **And much more**: Continuous improvements and new features on the way! 🌱✨

# 🛠️ Setup Guide

1. **Download and Extract the Repository** 📥  
   First, download the files from the repository and extract them to any location on your system.

2. **Install Python 3.10 or Higher** 🐍  
   Ensure that Python 3.10 or higher is installed on your machine. You can download it from the [official Python website](https://www.python.org/downloads/).

3. **Install Packages** 🔌  
   Open a Command Prompt (CMD) and run the following commands to install the following packages:
   ```bash
   python -m pip install Flask
   python -m pip install dnspython
   ```
   Flask and dnspython are the only packages that needed to be installed.

4. **Set Up Reverse Proxy (Recommended)** 🔒  
   Since the connection between Winget and the repository only works over HTTPS, it is recommended to set up a reverse proxy (e.g., Apache) in front of the repository for secure communication.

   **Alternative (Not Recommended)** ⚠️  
   If you choose not to set up a reverse proxy, you can use Flask’s built-in web server with HTTPS (though this is not recommended for production). To enable HTTPS on the Flask server, modify the `main.py` file as follows:
   ```python
   if __name__ == '__main__':
       app.run(ssl_context=('SSL/cert.pem', 'SSL/server.pem'))
   ```
   You will also need to create your own SSL certificates using tools like OpenSSL or similar.

6. **Accessing the Repository** 🌐  
   Once everything is set up, you should be able to access Winget-Repo under:
   ```
   https://localhost:5000
   ```
   Or any port you have configured for the server.

# 🔗 Connecting Winget with Winget-Repo

Once the Winget-Repo server is set up and accessible, you can now connect the Winget client to the server. Follow these steps:

1. **Open Command Prompt as Administrator** 🖥️  
   On the client that needs to connect to the Winget-Repo server, open a Command Prompt (CMD) with administrator rights.

2. **Add the Winget-Repo Source** ➕  
   In the Command Prompt, execute the following command:
   ```bash
   winget source add -n Winget-Repo -t "Microsoft.Rest" -a https://{URL of the server}/api/
   ```
   Replace `{URL of the server}` with the actual URL of your Winget-Repo server.

3. **Client authentication** 🔒  
   If client authentication is enabled on the server, include the following parameter: `--header "{'Token': '{ CLIENT_TOKEN }'}"`

   Replace `{CLIENT_TOKEN}` with the client token obtained from Client Management on the server.

   **Note:** The token must be included in every client request.

4. **Confirmation** ✅  
   If the setup is successful, you should see the following message:
   ```
   Source is being added:
     Winget-Repo -> https://{URL of the server}/api/
   Done
   ```

After completing these steps, your Winget-Repo should be ready to serve software and updates to clients within your local network!🎉


# 💬 Feedback

If you encounter any issues, have suggestions, or want to share improvements, please feel free to report them under the "Issues" section. Your feedback is valuable in helping us improve Winget-Repo and ensure it meets your needs. We appreciate your contributions and are here to assist with any challenges you may face!
[Report Issues and Features](https://github.com/dev-fYnn/Winget-Repo/issues)

And if you enjoy using Winget-Repo, we'd be grateful for a star ⭐ on our repository! Thank you for your support! 🙏
