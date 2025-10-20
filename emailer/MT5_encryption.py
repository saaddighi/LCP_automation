import os
from cryptography.fernet import Fernet
from emailer.email_sheet import sheet
import json
from dotenv import load_dotenv

load_dotenv()

FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise RuntimeError("Set FERNET_KEY environment variable first.")

f = Fernet(FERNET_KEY.encode())

def assign_account(id):
    credential_plain = {
    "username": "trader123",
    "password": "Sup3rS3cret!",
    "link":"https://example.com"
    }
    plaintext_bytes = json.dumps(credential_plain).encode()

    encrypted = f.encrypt(plaintext_bytes)
    encrypted_b64 = encrypted.decode()
    print(encrypted_b64)
    worksheet = sheet.get_all_values()

    for row in worksheet[1:]:
        if row[0] == id:
            sheet.update_cell(int(row[0]) + 1, 10, encrypted_b64)
            sheet.update_cell(int(row[0]) + 1, 11, "ok")
            print(f"Stored encrypted credentials for {row[1]} credential in Google Sheet.")
            print(row[0])

def decrypt_account(user_id):
    all_rows = sheet.get_all_values()

    for row in all_rows:
        if row and row[0] == user_id:
            if not row[9]:
                raise ValueError(f"No encrypted data found for {user_id}")

            encrypted_b64 = row[9]
            decrypted_bytes = f.decrypt(encrypted_b64.encode())
            credentials = json.loads(decrypted_bytes.decode())
            return credentials

    raise ValueError(f"User ID {user_id} not found in sheet.")