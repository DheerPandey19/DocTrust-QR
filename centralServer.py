import base64
import socket
import threading

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from utils import KEYS_DIR

hash_db: dict[str, str] = {}


def load_cs_private_key() -> RSA.RsaKey:
    with open(KEYS_DIR / "cs_private.pem", "rb") as f:
        return RSA.import_key(f.read())


def load_r_public_key() -> RSA.RsaKey:
    with open(KEYS_DIR / "r_public.pem", "rb") as f:
        return RSA.import_key(f.read())


def decrypt_with_cs_key(encrypted_data: str) -> str:
    private_key = load_cs_private_key()
    cipher = PKCS1_OAEP.new(private_key)
    decrypted_data = cipher.decrypt(base64.b64decode(encrypted_data))
    return decrypted_data.decode("utf-8")


def encrypt_for_recruiter(data: str) -> str:
    r_public_key = load_r_public_key()
    cipher = PKCS1_OAEP.new(r_public_key)
    encrypted_data = cipher.encrypt(data.encode("utf-8"))
    return base64.b64encode(encrypted_data).decode("utf-8")


def handle_client(conn: socket.socket, addr) -> None:
    try:
        data = conn.recv(4096).decode("utf-8")
        if not data:
            return

        action, roll_no, payload = data.split("|", 2)

        if action == "STORE":
            decrypted_hash = decrypt_with_cs_key(payload)
            hash_db[roll_no] = decrypted_hash
            print(f"[CS] Hash stored for roll number {roll_no} from {addr}")
        elif action == "FETCH":
            stored_hash = hash_db.get(roll_no, "NOT_FOUND")
            encrypted_for_r = encrypt_for_recruiter(stored_hash)
            conn.sendall(encrypted_for_r.encode("utf-8"))
            print(f"[CS] Hash fetched for roll number {roll_no} to {addr}")
        else:
            print(f"[CS] Invalid action from {addr}: {action}")
    finally:
        conn.close()


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 8000))
    server.listen(5)
    print("[CS] Central Server listening on localhost:8000")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
