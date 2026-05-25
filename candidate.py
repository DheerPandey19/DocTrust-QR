import base64
import socket
import sys
import zlib

import qrcode

from utils import (
    extract_text_from_pdf,
    recv_with_length,
    sample_path,
)


def generate_qr_code(data: str, output_image: str = "compressed_qr.png") -> str:
    compressed_data = zlib.compress(data.encode("utf-8"))
    encoded_data = base64.b64encode(compressed_data).decode("utf-8")
    qr = qrcode.QRCode(
        version=40,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(encoded_data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img.save(output_image)
    return output_image


def send_qr_and_roll_no_to_recruiter(image: str, roll_no: str) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", 8002))
        roll_no_encoded = roll_no.encode("utf-8") + b"\n"
        s.sendall(roll_no_encoded)

        with open(image, "rb") as f:
            qr_data = f.read()

        s.sendall(len(qr_data).to_bytes(4, "big"))
        s.sendall(qr_data)


def extract_tampered_documents(roll_no: str) -> str:
    resume_path = sample_path(roll_no, "resume1.pdf")
    marksheet_path = sample_path(roll_no, "marksheet.pdf")
    extracted_text = extract_text_from_pdf(resume_path)
    extracted_text += extract_text_from_pdf(marksheet_path)
    return extracted_text


def run_candidate(roll_no: str | None = None, forward_authentic: bool | None = None) -> None:
    roll_no = roll_no or input("Enter the Roll Number: ").strip()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", 8001))
        s.sendall(roll_no.encode("utf-8"))
        data = recv_with_length(s).decode("utf-8")

    if forward_authentic is None:
        option = input("Do you want to forward the data now? (y/n): ").strip().lower()
        forward_authentic = option == "y"
    elif forward_authentic:
        print("[Candidate] Forwarding authentic institute data")
    else:
        print("[Candidate] Using tampered documents")

    if not forward_authentic:
        data = extract_tampered_documents(roll_no)

    with open("candi_file.txt", "w", encoding="utf-8") as f:
        f.write(data)

    qr_image_path = generate_qr_code(data)
    send_qr_and_roll_no_to_recruiter(qr_image_path, roll_no)
    print(f"[Candidate] QR code sent to recruiter for roll number {roll_no}")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        run_candidate(sys.argv[1], sys.argv[2].lower() == "y")
    else:
        run_candidate()
