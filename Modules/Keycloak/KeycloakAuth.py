import uuid
import jwt
from flask import current_app

import settings
from Modules.User.Functions import add_User, check_User_Exists

try:
    from keycloak import KeycloakOpenID
    KEYCLOAK_AVAILABLE = True
except ImportError:
    KEYCLOAK_AVAILABLE = False
    KeycloakOpenID = None


class KeycloakAuthenticator:
    def __init__(self):
        self.server_url = settings.KEYCLOAK_SERVER_URL
        self.realm_name = settings.KEYCLOAK_REALM_NAME
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self.redirect_uri = settings.KEYCLOAK_REDIRECT_URI
        self.post_logout_redirect_uri = settings.KEYCLOAK_POST_LOGOUT_REDIRECT_URI
        self.default_group = settings.KEYCLOAK_DEFAULT_GROUP
        
        if settings.KEYCLOAK_ENABLED and KEYCLOAK_AVAILABLE:
            self.keycloak_openid = KeycloakOpenID(
                server_url=self.server_url,
                client_id=self.client_id,
                realm_name=self.realm_name,
                client_secret_key=self.client_secret
            )
        else:
            self.keycloak_openid = None

    def is_enabled(self):
        """Check if Keycloak authentication is enabled"""
        return settings.KEYCLOAK_ENABLED and KEYCLOAK_AVAILABLE and self.keycloak_openid is not None

    def get_auth_url(self, state=None):
        """Generate the authorization URL for Keycloak login"""
        if not self.is_enabled():
            return None
            
        auth_url = self.keycloak_openid.auth_url(
            redirect_uri=self.redirect_uri,
            scope="openid email profile",
            state=state
        )
        return auth_url

    def get_logout_url(self):
        """Generate the logout URL for Keycloak logout"""
        if not self.is_enabled():
            return None
            
        logout_url = f"{self.server_url}/realms/{self.realm_name}/protocol/openid-connect/logout"
        logout_url += f"?post_logout_redirect_uri={self.post_logout_redirect_uri}"
        logout_url += f"&client_id={self.client_id}"
        
        return logout_url

    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        if not self.is_enabled():
            return None
            
        try:
            token = self.keycloak_openid.token(
                grant_type='authorization_code',
                code=code,
                redirect_uri=self.redirect_uri
            )
            return token
        except Exception as e:
            current_app.logger.error(f"Error exchanging code for token: {e}")
            return None

    def get_user_info(self, token):
        """Get user information from Keycloak token"""
        if not self.is_enabled():
            return None
            
        try:
            userinfo = self.keycloak_openid.userinfo(token['access_token'])
            return userinfo
        except Exception as e:
            current_app.logger.error(f"Error getting user info: {e}")
            return None

    def decode_token(self, token):
        """Decode JWT token to get user information"""
        if not self.is_enabled():
            return None
            
        try:
            # Get the key to verify the token
            key = self.keycloak_openid.public_key()
            key = f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"
            
            # Decode the token
            decoded_token = jwt.decode(
                token['access_token'],
                key,
                algorithms=['RS256'],
                audience=self.client_id,
                options={"verify_signature": True, "verify_aud": True, "verify_exp": True}
            )
            return decoded_token
        except Exception as e:
            current_app.logger.error(f"Error decoding token: {e}")
            return None

    def create_or_update_user(self, user_info):
        """Create or update user in local database from Keycloak user info"""
        try:
            # Extract user information
            username = user_info.get('preferred_username') or user_info.get('sub')
            
            if not username:
                current_app.logger.error("No username found in Keycloak user info")
                return False, None
            
            # Check if user already exists
            user_exists, user_data = check_User_Exists(username)
            
            if user_exists:
                # User exists, return user ID
                return True, user_data.get('ID')
            else:
                # Create new user
                # Generate a random password (won't be used for Keycloak users)
                dummy_password = str(uuid.uuid4())
                
                # Add user to database with default group
                success = add_User(username, dummy_password, self.default_group, deletable=1)
                
                if success:
                    # Get the newly created user ID
                    user_exists, user_data = check_User_Exists(username)
                    if user_exists:
                        return True, user_data.get('ID')
                    else:
                        current_app.logger.error("Failed to retrieve newly created user")
                        return False, None
                else:
                    current_app.logger.error("Failed to create user in database")
                    return False, None
                    
        except Exception as e:
            current_app.logger.error(f"Error creating/updating user: {e}")
            return False, None

    def validate_token(self, token):
        """Validate if the token is still valid"""
        if not self.is_enabled():
            return False
            
        try:
            # Try to get user info with the token
            userinfo = self.get_user_info(token)
            return userinfo is not None
        except Exception as e:
            current_app.logger.error(f"Error validating token: {e}")
            return False


# Global instance
keycloak_auth = KeycloakAuthenticator()
