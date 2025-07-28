# ⚙️ Winget-Repo Server Settings Overview

This document describes the configuration options available in the **Winget-Repo Server Settings** panel.

---

## 🔧 Server Settings Table

| **Name**                                      | **Description**                                                                 |
|----------------------------------------------|---------------------------------------------------------------------------------|
| **Server Name (Max. 12)**                    | Sets the name of your Winget server (max 12 characters). Appears in the UI.    |
| **Winget-Client Versions**                   | Lists the compatible Winget client versions separated by commas.               |
| **Client Authentication**                    | Enables client-side authentication for secure access.                          |
| **DNS Server**                               | IP address of the DNS server used for client resolution and authentication.    |
| **Domain Suffix**                            | The DNS suffix applied to clients during authentication. (e.g. fritz.box)      |
| **Enable Terms of Service**                  | Option to enable/require acceptance of Terms of Service for the winget client. |
| **Enable Package Store (Internet required)** | Enables online package store integration (requires internet access).           |

---

## 💡 Notes

- **Client Authentication** must be enabled if you want to restrict repository access based on trusted clients.
- Ensure the **DNS Server** and **Domain Suffix** match your internal network setup.

---

