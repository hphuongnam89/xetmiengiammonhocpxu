# Production configuration gate

Production startup requires `APP_ENV=production`, `DEBUG=false`, a random `SECRET_KEY` (50+ characters), explicit `ALLOWED_HOSTS`, PostgreSQL, TLS-enabled Redis, database credentials, and an installed private object-storage backend. Local filesystem storage is rejected for production. The example is `app/backend/.env.example`; replace every placeholder and use a secret manager for real credentials.

Production enables secure session/CSRF cookies, a 10-attempt/15-minute IP login throttle backed by Redis, HTTPS redirect, and one-hour HSTS by default. Set `SECURE_BEHIND_PROXY=true` only when a trusted TLS proxy strips incoming forwarded-proto headers and sets `X-Forwarded-Proto` itself. Leave HSTS subdomains and preload disabled until every affected subdomain is verified HTTPS-only and the domain owner authorizes preload.

Before release, provision PostgreSQL, private encrypted object storage, TLS/proxy, backups and restore testing, secret rotation, dependency audit, monitoring, and an admin account with MFA. Never point production at the local SQLite database or media directory.
