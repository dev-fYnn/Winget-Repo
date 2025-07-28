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