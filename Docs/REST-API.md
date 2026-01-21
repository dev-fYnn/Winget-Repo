# 🚀 Winget-Repo REST API Documentation

## 1. Overview
This document provides a complete overview of all available REST API endpoints for the **Winget-Repo** service.

## 📑 Documentation
1. Login to Winget-Repo
2. Open the Server Settings
3. Click the Ethernet Symbol in the upper right corner

---

## 2. Authentication Mechanisms

### 2.1 Administrator Authentication (Bearer)
* **Usage**: Required for modifying data (Add/Edit/Delete packages).
* **Verification**: `HTTPBearer` - Bearer Token without usage has a 1 hour lifetime 

### 2.2 Client Authentication (Auth-Token)
* **Usage**: Used by the Winget Client to fetch packages.
* **Logic**: If `CLIENT_AUTHENTICATION` is enabled in settings, the API verifies the `auth_token`. It also checks if the specific client IP/Token combination is blacklisted.

---

## 3. Endpoint Reference

### 3.1 Authentication & Session

### `POST /{tenant_id}/login`
Authenticates a dashboard user and creates a rest session.

* **Tags**: `Authentication`
* **Content-Type**: `application/x-www-form-urlencoded`
* **Parameters**:
    * `username` (Form, str, required)
    * `password` (Form, str, required)
* **Responses**:
    * `200 OK`: `{"message": "<session_token_string>"}`
    * `401 Unauthorized`: Invalid credentials.

### `POST /{tenant_id}/logout`
Invalidates a specific session token.

* **Tags**: `Authentication`
* **Parameters**:
    * `token` (Form, str, required): The session token to destroy.
* **Responses**:
    * `200 OK`: `{"message": "Logout Successful!"}`

### `GET /{tenant_id}/test`
Simple heartbeat to verify Bearer token validity.

* **Tags**: `Authentication`
* **Headers**:
    * `Authorization`: `Bearer <token>`
* **Responses**:
    * `200 OK`: `{"Message": "Its working!"}`

---

## 3.2 Client Operations

### `POST /{tenant_id}/client_version`
Retrieves the latest version of the Winget-Repo Client executable.

* **Tags**: `Winget-Repo Client`
* **Security Logic**:
    1.  Checks `Bearer` token (Admin access).
    2.  If failing, checks `auth_token` (Client access) if authentication is enforced settings.
* **Parameters**:
    * `auth_token` (Form, str, optional): Client specific token.
    * `client` (Form, int, optional): Client ID (default 0).
* **Responses**:
    * `200 OK`: `{"Version": "2.5.0.0"}`
    * `401 Unauthorized`: If authentication is enabled and fails.

### `POST /{tenant_id}/get_packages`
Retrieves the full catalog of packages.

* **Tags**: `Packages`
* **Description**: Returns packages, available versions, and **Base64 encoded** logos. Applies "Blacklist" filtering if accessed via Client Auth-Token.
* **Parameters**:
    * `include_disabled` (Query, bool, default `False`): If true, returns inactive packages.
    * `auth_token` (Form, str, optional).
    * `client` (Form, int, optional).
* **Responses**:
    * `200 OK`: JSON Array of [Package Object](#51-package-object).

---

## 3.3 Package Management (Admin Only)

**Requires:** `Authorization: Bearer <token>`

### `POST /{tenant_id}/add_package`
Creates a new package entry in the database.

* **Tags**: `Packages`
* **Parameters**:
    * `package_id` (Form, str): Unique identifier (e.g., `Mozilla.Firefox`).
    * `package_name` (Form, str)
    * `package_publisher` (Form, str)
    * `package_description` (Form, str)
    * `Logo` (File, UploadFile, optional): PNG/JPG file.
* **Responses**:
    * `200 OK`: `{"Message": "Package was added successfully!"}`
    * `401`: Package ID already exists or creation failed.

### `PATCH /{tenant_id}/edit_package/{package_id}`
Modifies an existing package's metadata or logo.

* **Tags**: `Packages`
* **Path Parameters**:
    * `package_id`: The ID of the package to edit.
* **Form Parameters**:
    * `package_name`, `package_publisher`, `package_description`
    * `Logo` (File, Optional)
* **Responses**:
    * `200 OK`: `{"Message": "Package was updated successfully!"}`
    * `404`: Package not found.

### `DELETE /{tenant_id}/delete_package/{package_id}`
Deletes a package and **all** associated versions and files.

* **Tags**: `Packages`
* **Responses**:
    * `200 OK`: `{"Message": "Package was deleted successfully!"}`

---

## 3.4 Package Version Control

### `GET /{tenant_id}/get_package_versions/{package_id}`
Retrieves all versions associated with a package ID.

* **Tags**: `Package Versions`
* **Responses**:
    * `200 OK`: Array of [Package_Version Object](#52-package_version-object). Includes nested installer paths if applicable.

### `GET /{tenant_id}/get_specific_package_version/{version_uid}`
Retrieves details for a single version using its unique UUID.

* **Tags**: `Package Versions`
* **Responses**:
    * `200 OK`: Single [Package_Version Object](#52-package_version-object).

### `DELETE /{tenant_id}/delete_package_version/{package_id}`
Deletes specific versions of a package.

* **Tags**: `Package Versions`
* **Parameters**:
    * `versions_uids` (Form, List[str]): A list of UUIDs or a comma-separated string of UUIDs.
* **Responses**:
    * `200 OK`: `{"Message": "Package versions deleted successfully!"}`

---

## 3.5 Add Package Version

### `POST /{tenant_id}/add_package_version/{package_id}`
Create a new package version

* **Tags**: `Package Versions`
* **Parameters**:
    * `file` (file): Upload the installer file
    * **Metadata (Form)**:
        * `package_version`: (e.g., "1.0.0")
        * `file_architect`: [Enum Architecture](#61-enums)
        * `file_type`: [Enum FileType](#61-enums)
        * `file_scope`: [Enum Scope](#61-enums)
        * `package_locale`: [Enum Locale](#61-enums)
        * `channel`: (Default: "stable")
    * **Switches (Optional Form)**:
        * `switch_Silent`, `switch_Interactive`, `switch_Log`, `switch_Upgrade`, `switch_Custom`, `switch_Repair`
    * **Advanced (Optional Form)**:
        * `productcode`, `upgradecode`, `package_family_name`, `file_type_nested`, `file_nested_path`
* **Responses**:
    * `201 Created`: `{"Message": "...", "UID": "<new_version_uid>"}`
    * `409 Conflict`: Version already exists.
    * `407`: Storage quota exceeded.

---

## 4. Response Models

## 4.1 Package Object
```json
{
  "PACKAGE_ID": "string",
  "PACKAGE_NAME": "string",
  "PACKAGE_PUBLISHER": "string",
  "PACKAGE_DESCRIPTION": "string",
  "PACKAGE_LOGO": "data:image/png;base64,.....",
  "PACKAGE_ACTIVE": "string (1 or 0)",
  "VERSIONS": ["1.2.0", "1.1.0"],
  "VERSIONS_UID": ["uuid-string-1", "uuid-string-2"]
}
```

## 4.2 Package_Version Object (Response)
```json
{
  "PACKAGE_ID": "Google.Chrome",
  "VERSION": "120.0.1",
  "LOCALE": "en-US",
  "ARCHITECTURE": "x64",
  "INSTALLER_TYPE": "MSI",
  "INSTALLER_URL": "Download_Url",
  "INSTALLER_SHA256": "e3b0c44298fc1c149afbf4c8996fb...",
  "INSTALLER_SCOPE": "machine",
  "UID": "a1b2c3d4-e5f6...",
  "INSTALLER_NESTED_TYPE": "EXE",
  "PRODUCTCODE": "{GUID}",
  "UPGRADECODE": "{GUID}",
  "PACKAGE_FAMILY_NAME": "Chrome_Package",
  "CHANNEL": "stable",
  "NESTED_PACKAGE_INSTALLER_PATHS": []
}
```
---

## 5. Enums & Constants

## 5.1 Detailed Enums
* Architecture: x64, x86
* FileType: EXE, MSI, MSIX, APPX, ZIP, INNO, NULLSOFT, WIX, BURN
* Scope: machine, user
* Locale: en-US, de-DE, de-AT, de-CH, en-GB, en-CA, en-AU, fr-FR, fr-CA, fr-BE, es-ES, es-MX, it-IT, it-CH, pt-PT, pt-BR, ja-JP, ko_KR, zh_CN, zh_TW

---

## 6. Error Codes Summary
| Status Code | Meaning | Detailed Reason                |
|:------------|:--------|:-------------------------------|
| 200         | Success | Request completed successfully |
| 201         | Resource Created        | Package version successfully added to the system |
| 307         | Temporary Redirect    | Documentation access redirected via Authentication check (Middleware) |
| 400         | Bad Request   | Missing data, required headers (X-File-ID), or invalid chunk format. |
| 401         | Unauthorized   | Invalid, expired, or missing Token/Credentials. |
| 403         | Forbidden    | The Client IP address is not authorized for this specific tenant |
| 404         | Not Found   | The requested Tenant, Package, or Version UID does not exist. |
| 407         | Storage Exceeded  | Tenant storage limit reached (Proxy Auth context) |
| 409         | Conflict  | Version or Package ID already exists in the database |
| 500         | Internal Server Error | Generic error, chunk processing failure, or database connection issue. |
