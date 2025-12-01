# 🚀 Winget-Repo REST API Documentation

This document provides a complete overview of all available REST API endpoints for the **Winget-Repo** service.

## 📑 Documentation
1. Login to Winget-Repo
2. Open the Server Settings
3. Click the Ethernet Symbol in the upper right corner

## 🔐 Authentication

### **POST /login**

Authenticate a user and receive a **Bearer token**. 
- Token lifetime: **1 hour** 
- Token is suspended after **1 hour of inactivity**

### **POST /logout**

Invalidate the currently active Bearer token.

### **GET /test**

Check API availability and validate Bearer authentication. 
- **Requires Bearer Token**

## 🖥️ Winget-Repo Client

### **POST /client_version**

Retrieve the latest Winget-Repo Client version. 
- **Requires Bearer Token**
- Also requires **Client Authentication Token** when client authentication is enabled

## 📦 Packages

### **POST /get_packages**

Retrieve all packages including versions and Base64-encoded logos.
- **Requires Bearer Token** 
- Also requires **Client Authentication Token** when enabled

### **POST /add_package**

Create a new package. 
- **Requires Bearer Token**

### **PATCH /edit_package/{package_id}**

Edit an existing package. 
- **Requires Bearer Token**

### **DELETE /delete_package/{package_id}**

Delete a package. 
- **Requires Bearer Token**

## 🔢 Package Versions

### **GET /get_package_versions/{package_id}**

Retrieve all versions of a specific package. 
- **Requires Bearer Token**

### **GET /get_specific_package_version/{version_uid}**

Retrieve detailed information about a specific package version. 
- **Requires Bearer Token**

### **POST /add_package_version/{package_id}**

Add a new version to an existing package. 
- **Requires Bearer Token**

### **DELETE /delete_package_version/{package_id}**

Delete one or multiple package versions. 
- **Requires Bearer Token**
