import os
import secrets
import subprocess

def create_env():
    print("Setting up WaSphere environment...")
    base = r"C:\Users\Ashley\wasphere"
    env_file = os.path.join(base, ".env")
    
    # Generate secrets
    jwt_secret = secrets.token_hex(32)
    enc_key = secrets.token_hex(32)
    wa_token = secrets.token_hex(32)
    webhook_secret = secrets.token_hex(32)
    internal_webhook = secrets.token_hex(32)
    
    env_content = f"""POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DB=wasphere
JWT_SECRET={jwt_secret}
ENCRYPTION_KEY={enc_key}
WA_TOKEN={wa_token}
WEBHOOK_SIGNING_SECRET={webhook_secret}
INTERNAL_WEBHOOK_SECRET={internal_webhook}
DASHBOARD_UI_URL=http://localhost:3004
DATABASE_URL=postgresql://postgres@localhost:5432/wasphere?schema=public
"""
    
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)
    print("Created .env with secure random keys.")

if __name__ == "__main__":
    create_env()
