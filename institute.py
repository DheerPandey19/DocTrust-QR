import base64
import socket

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from utils import (
    KEYS_DIR,
    extract_text_from_pdf,
    hash_data,
    sample_path,
    send_with_length,
)


def load_cs_public_key() -> RSA.RsaKey:
    with open(KEYS_DIR / "cs_public.pem", "rb") as f:
        return RSA.import_key(f.read())


def encrypt_with_cs_key(data: str) -> str:
    cs_public_key = load_cs_public_key()
    cipher = PKCS1_OAEP.new(cs_public_key)
    encrypted_data = cipher.encrypt(data.encode("utf-8"))
    return base64.b64encode(encrypted_data).decode("utf-8")


def send_to_central_server(roll_no: str, hashed_value: str) -> None:
    encrypted_hash = encrypt_with_cs_key(hashed_value)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", 8000))
        message = f"STORE|{roll_no}|{encrypted_hash}"
        s.sendall(message.encode("utf-8"))


def extract_candidate_documents(roll_no: str) -> str:
    resume_path = sample_path(roll_no, "resume.pdf")
    marksheet_path = sample_path(roll_no, "marksheet.pdf")
    extracted_text = extract_text_from_pdf(resume_path)
    extracted_text += extract_text_from_pdf(marksheet_path)
    return extracted_text


def serve_candidate() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 8001))
    server.listen(5)
    print("[Institute] Listening on localhost:8001")

    while True:
        conn, addr = server.accept()
        try:
            roll_no = conn.recv(1024).decode("utf-8").strip()
            if not roll_no:
                print(f"[Institute] Ignoring empty request from {addr}")
                continue

            print(f"[Institute] Request from {addr} for roll number {roll_no}")
            extracted_text = extract_candidate_documents(roll_no)

            with open("insti_file.txt", "w", encoding="utf-8") as f:
                f.write(extracted_text)

            send_with_length(conn, extracted_text.encode("utf-8"))
            hashed_value = hash_data(extracted_text)
            send_to_central_server(roll_no, hashed_value)
            print(f"[Institute] Documents processed and hash stored for {roll_no}")
        except Exception as exc:
            print(f"[Institute] Error handling {addr}: {exc}")
        finally:
            conn.close()


if __name__ == "__main__":
    serve_candidate()
