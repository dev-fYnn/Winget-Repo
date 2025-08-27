# Keycloak Integration Setup

This document describes how to set up Keycloak authentication for Winget-Repo.

## Prerequisites

- Keycloak server running and accessible
- Admin access to Keycloak server
- Python packages: `python-keycloak` and `PyJWT`

## Installation

1. Install the required Python packages:
   ```bash
   pip install python-keycloak PyJWT
   ```

## Keycloak Server Configuration

### 1. Create a Realm

1. Log in to the Keycloak Admin Console
2. Click on "Add realm" or select an existing realm
3. Enter realm name (e.g., `winget-repo`)
4. Click "Create"

### 2. Create a Client

1. Go to Clients → Create
2. Set the following values:
   - **Client ID**: `winget-repo-client`
   - **Client Protocol**: `openid-connect`
3. Go to next step

### 3. Configure Client Settings

1. In the client settings, set:
   - **Client Authentication**: `ON`
   - **Authorization**: `OFF`
   - **Standard flow**: `ON`
   - **Direct Access Grants Enabled**: `OFF`
2. In the next step (_login settings_), set:
   - **Root URL**: `http://localhost:5000`
   - **Home URL**: `http://localhost:5000`
   - **Valid Redirect URIs**: `http://localhost:5000/keycloak/callback`
   - **Valid Post logout redirect URIs**: `http://localhost:5000/`
   - **Web origins**: `http://localhost:5000`
2. Click "Save"
3. Go to "Credentials" tab and copy the "Secret" value

### 4. Create Users (Optional)

1. Go to Users → Add user
2. Fill in user details
3. Go to "Credentials" tab and set a password
4. Set "Temporary" to OFF

## Winget-Repo Configuration

Set the following environment variables or modify `settings.py`:

```bash
# Enable Keycloak authentication
export KEYCLOAK_ENABLED=true

# Keycloak server configuration
export KEYCLOAK_SERVER_URL=http://localhost:8080
export KEYCLOAK_REALM_NAME=winget-repo
export KEYCLOAK_CLIENT_ID=winget-repo-client
export KEYCLOAK_CLIENT_SECRET=your-client-secret-from-keycloak

# Redirect URI (must match the one configured in Keycloak client)
export KEYCLOAK_REDIRECT_URI=http://localhost:5000/keycloak/callback

# Post-logout redirect URI (must match the one configured in Keycloak client)
export KEYCLOAK_POST_LOGOUT_REDIRECT_URI=http://localhost:5000/

# Default group ID for new Keycloak users (admin group by default)
export KEYCLOAK_DEFAULT_GROUP=f4b8b5af-a414-466f-aad9-184e7e386425
```

### Alternative: Direct Configuration in settings.py

If you prefer not to use environment variables, you can modify `settings.py` directly.

## How It Works

1. **SSO Redirect**: When users visit the login page and Keycloak is enabled, they are automatically redirected to Keycloak for authentication
2. **User Creation**: Upon successful authentication, the system automatically creates a local user account
3. **Session Management**: Users authenticated via Keycloak are tracked in the session
4. **Permissions**: New Keycloak users are assigned to the default group (admin by default)
5. **Local Login Bypass**: Access `/local` to use traditional username/password login if needed

## Security Features

- **CSRF Protection**: State parameter validation prevents CSRF attacks
- **Token Validation**: JWT tokens are properly validated
- **Secure Sessions**: Keycloak tokens are stored securely in Flask sessions
- **Automatic SSO**: Seamless redirect to Keycloak when enabled

## Troubleshooting

### Common Issues

1. **"Import keycloak could not be resolved"**
   - Install the package: `pip install python-keycloak`

2. **"Keycloak authentication is not enabled"**
   - Set `KEYCLOAK_ENABLED=true` in environment variables or settings.py

3. **"Invalid redirect URI"**
   - Ensure the redirect URI in Keycloak client matches `KEYCLOAK_REDIRECT_URI`

4. **"Failed to exchange code for token"**
   - Check client secret and server URL configuration
   - Verify Keycloak server is accessible

### Accessing Local Login

If you need to bypass SSO and use local authentication:
- Navigate to `/login/local` instead of `/login`
- This shows the traditional username/password form

## Production Considerations

1. **HTTPS**: Use HTTPS in production for secure token transmission
2. **Client Secret**: Store client secret securely (environment variables or secret management)
3. **Logout**: Consider implementing proper Keycloak logout flow
4. **Token Refresh**: Implement token refresh for long-running sessions
5. **Group Mapping**: Map Keycloak groups/roles to local permissions

## Disabling Keycloak

To disable Keycloak authentication:

```bash
export KEYCLOAK_ENABLED=false
```

Or in `settings.py`:

```python
KEYCLOAK_ENABLED = False
```

The application will fall back to traditional username/password authentication.
