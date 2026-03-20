---
name: sso-integration
description: SSO Integration for methodology-v2. Use when: (1) Adding SAML authentication, (2) OAuth2/Google login, (3) LDAP directory integration, (4) Enterprise single sign-on. Provides unified SSO interface.
---

# SSO Integration

Enterprise single sign-on for methodology-v2.

## Quick Start

```python
from sso_integration import SSOManager, SAMLConfig, OAuthConfig

# SAML Configuration
saml = SAMLConfig(
    idp_metadata_url="https://idp.example.com/metadata",
    sp_entity_id="https://app.methodology.cloud",
    acs_url="https://app.methodology.cloud/saml/acs"
)

# OAuth Configuration
oauth = OAuthConfig(
    provider="google",
    client_id="xxx",
    client_secret="xxx",
    redirect_uri="https://app.methodology.cloud/oauth/callback"
)

# Initialize SSO Manager
sso = SSOManager()
sso.add_provider("saml", saml)
sso.add_provider("oauth", oauth)

# Login
auth_url = sso.get_login_url("oauth")
# Redirect user to auth_url

# Callback
user = sso.handle_callback("oauth", code)
```

## Supported Providers

### 1. SAML 2.0

```python
from sso_integration import SAMLConfig

saml = SAMLConfig(
    idp_metadata_url="https://okta.example.com/app/abc/sso/saml",
    sp_entity_id="https://myapp.com",
    acs_url="https://myapp.com/saml/acs",
    attribute_mapping={
        "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
    }
)
```

### 2. OAuth2

```python
from sso_integration import OAuthConfig

# Google
google = OAuthConfig(
    provider="google",
    client_id="xxx",
    client_secret="xxx",
    redirect_uri="https://myapp.com/oauth/google/callback",
    scopes=["openid", "email", "profile"]
)

# GitHub
github = OAuthConfig(
    provider="github",
    client_id="xxx",
    client_secret="xxx",
    redirect_uri="https://myapp.com/oauth/github/callback",
    scopes=["read:user", "user:email"]
)

# Microsoft
microsoft = OAuthConfig(
    provider="microsoft",
    client_id="xxx",
    client_secret="xxx",
    redirect_uri="https://myapp.com/oauth/microsoft/callback"
)
```

### 3. LDAP

```python
from sso_integration import LDAPConfig

ldap = LDAPConfig(
    server="ldap://ldap.example.com",
    port=389,
    base_dn="dc=example,dc=com",
    bind_dn="cn=admin,dc=example,dc=com",
    bind_password="xxx",
    user_filter="(uid={username})",
    group_filter="(memberUid={username})"
)
```

## Usage

### Login Flow

```python
# Step 1: Redirect to identity provider
auth_url = sso.login(
    provider="google",
    redirect_uri="https://myapp.com/dashboard"
)

# Step 2: Handle callback
user = sso.handle_callback(
    provider="google",
    code="authorization_code",
    state="csrf_state"
)

print(f"Logged in as: {user.email}")
```

### Session Management

```python
# Create session
session = sso.create_session(user)
session_id = session.id

# Validate session
if sso.validate_session(session_id):
    # Access granted
    pass

# Logout
sso.logout(session_id)
```

## RBAC Integration

```python
from sso_integration import RBACSSO

rbac_sso = RBACSSO(sso_manager=sso)

# Define roles
rbac_sso.add_role("admin", ["read", "write", "delete"])
rbac_sso.add_role("developer", ["read", "write"])
rbac_sso.add_role("viewer", ["read"])

# Assign role to user
rbac_sso.assign_role(user.id, "developer")

# Check permission
if rbac_sso.has_permission(user.id, "write"):
    # Allow action
    pass
```

## Configuration

```python
# SSO Configuration
SSO_CONFIG = {
    "providers": {
        "saml": {
            "enabled": True,
            "idp_metadata_url": "https://idp.example.com/metadata"
        },
        "oauth": {
            "google": {"enabled": True},
            "github": {"enabled": True},
            "microsoft": {"enabled": False}
        },
        "ldap": {
            "enabled": True,
            "server": "ldap://ldap.example.com"
        }
    },
    "session": {
        "ttl": 3600,  # 1 hour
        "refresh_enabled": True
    }
}
```

## CLI Usage

```bash
# Test SSO configuration
python sso_integration.py test --provider google

# Generate SP metadata (for SAML)
python sso_integration.py metadata --output sp_metadata.xml

# Validate certificates
python sso_integration.py validate --cert idp.crt
```

## Security

| Feature | Description |
|--------|-------------|
| Token Validation | Verify JWT signatures |
| CSRF Protection | State parameter validation |
| Session Security | HttpOnly, Secure cookies |
| Certificate Pinning | Pin IdP certificates |

## Best Practices

1. **Use HTTPS** - Always use TLS
2. **Validate certificates** - Check IdP certificates
3. **Session TTL** - Set reasonable session expiry
4. **Logout** - Invalidate sessions on logout

## See Also

- [rbac.py](rbac.py) - Role-based access control
- [security_audit.py](security_audit.py) - Security auditing
