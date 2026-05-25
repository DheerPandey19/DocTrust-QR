import base64
import socket
import sys
import zlib
from pathlib import Path

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from PIL import Image

from utils import KEYS_DIR, PROJECT_ROOT, hash_data, recv_all

QR_IMAGE_PATH = PROJECT_ROOT / "received_qr.png"


def check_pyzbar() -> None:
    try:
        from pyzbar.pyzbar import decode  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "pyzbar is not installed. Run: pip install -r requirements.txt"
        ) from exc


def load_r_private_key() -> RSA.RsaKey:
    with open(KEYS_DIR / "r_private.pem", "rb") as f:
        return RSA.import_key(f.read())


def decrypt_with_r_key(encrypted_data: str) -> str:
    private_key = load_r_private_key()
    cipher = PKCS1_OAEP.new(private_key)
    decrypted_data = cipher.decrypt(base64.b64decode(encrypted_data))
    return decrypted_data.decode("utf-8")


def decode_qr(image_path: Path) -> str | None:
    from pyzbar.pyzbar import decode

    img = Image.open(image_path)
    decoded_objects = decode(img)

    if not decoded_objects:
        return None

    qr_data = decoded_objects[0].data.decode("utf-8", errors="ignore")
    try:
        compressed_data = base64.b64decode(qr_data)
        return zlib.decompress(compressed_data).decode("utf-8")
    except Exception:
        return None


def fetch_hash_from_cs(roll_no: str) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cs:
        cs.connect(("localhost", 8000))
        request = f"FETCH|{roll_no}|NULL"
        cs.sendall(request.encode("utf-8"))
        encrypted_hash = cs.recv(4096).decode("utf-8")
    return decrypt_with_r_key(encrypted_hash)


def verify_candidate() -> bool | None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 8002))
    server.listen(1)
    print("[Recruiter] Listening on localhost:8002")

    conn, addr = server.accept()
    print(f"[Recruiter] Connection from {addr}")

    roll_no_data = b""
    while not roll_no_data.endswith(b"\n"):
        chunk = conn.recv(1)
        if not chunk:
            break
        roll_no_data += chunk

    roll_no = roll_no_data.strip().decode("utf-8")
    file_size = int.from_bytes(recv_all(conn, 4), "big")
    qr_data = recv_all(conn, file_size)

    QR_IMAGE_PATH.write_bytes(qr_data)
    conn.close()
    server.close()

    qr_content = decode_qr(QR_IMAGE_PATH)
    if not qr_content:
        print("[Recruiter] Failed to decode QR code")
        return None

    with open("rec_file.txt", "w", encoding="utf-8") as f:
        f.write(qr_content)

    computed_hash = hash_data(qr_content)
    stored_hash = fetch_hash_from_cs(roll_no)

    if stored_hash == "NOT_FOUND":
        print("[Recruiter] No stored hash found for this roll number.")
        return False

    if computed_hash == stored_hash:
        print("[Recruiter] Verification Successful! The QR data is authentic.")
        return True

    print("[Recruiter] Verification Failed! The QR data is modified or incorrect.")
    return False


def main() -> None:
    check_pyzbar()
    result = verify_candidate()
    if len(sys.argv) > 1 and sys.argv[1] == "--expect":
        expected = sys.argv[2]
        if expected == "success" and result is not True:
            raise SystemExit(1)
        if expected == "fail" and result is not False:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
