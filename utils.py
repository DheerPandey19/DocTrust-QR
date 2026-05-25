import hashlib
import re
import socket
from pathlib import Path

import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLES_DIR = PROJECT_ROOT / "samples"
KEYS_DIR = PROJECT_ROOT / "keys"


def clean_text(text: str) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_pdf(input_pdf: str | Path) -> str:
    extracted_text = ""
    with pdfplumber.open(input_pdf) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text
    return clean_text(extracted_text)


def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def recv_all(sock: socket.socket, nbytes: int) -> bytes:
    chunks = []
    received = 0
    while received < nbytes:
        chunk = sock.recv(min(65536, nbytes - received))
        if not chunk:
            raise ConnectionError("Socket closed before all data was received")
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def send_with_length(sock: socket.socket, data: bytes) -> None:
    sock.sendall(len(data).to_bytes(4, "big"))
    sock.sendall(data)


def recv_with_length(sock: socket.socket) -> bytes:
    length_bytes = recv_all(sock, 4)
    length = int.from_bytes(length_bytes, "big")
    return recv_all(sock, length)


def sample_path(roll_no: str, suffix: str) -> Path:
    return SAMPLES_DIR / f"{roll_no}_{suffix}"
