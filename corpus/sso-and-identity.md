---
title: SSO and Identity Guide
access: internal
owner: Identity Engineering
---
# SSO and Identity

## Supported protocols
The corporate IdP is Okta. Applications integrate with SAML 2.0 or OpenID Connect (authorization code flow with PKCE). Legacy basic authentication is prohibited.

## Sessions
Interactive sessions expire after 8 hours of activity or 30 minutes of inactivity. Privileged sessions expire after 1 hour and require step-up MFA.

## Service and agent identities
AI agents must act on behalf of the signed-in user using OAuth 2.0 token exchange. Shared admin service accounts for agents are not allowed. Machine-to-machine credentials rotate every 90 days and are stored in the enterprise vault.

## Regional access
Service agents may only view cases belonging to their assigned region. Region is an attribute in the SAML assertion named `region`.
