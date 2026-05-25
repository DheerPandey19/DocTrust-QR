from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from utils import SAMPLES_DIR

ROLL_NO = "22CSB0F23"


def write_pdf(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 72
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y, title)
    y -= 36
    c.setFont("Helvetica", 11)
    for line in body.splitlines():
        c.drawString(72, y, line)
        y -= 16
        if y < 72:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 72
    c.save()


def main() -> None:
    resume_text = (
        "Name: Dheer Pandey\n"
        "Roll Number: 22CSB0F23\n"
        "Degree: B.Tech Computer Science\n"
        "Skills: Python, Cryptography, Networking\n"
        "Project: Secure Document Verification System"
    )
    resume1_text = (
        "Name: Dheer Pandey\n"
        "Roll Number: 22CSB0F23\n"
        "Degree: B.Tech Computer Science\n"
        "Skills: Python, Machine Learning, Cloud\n"
        "Project: Fake Portfolio Website"
    )
    marksheet_text = (
        "Institute: Example Institute of Technology\n"
        "Roll Number: 22CSB0F23\n"
        "Semester 1: 9.1\n"
        "Semester 2: 9.3\n"
        "Semester 3: 9.0\n"
        "Semester 4: 9.4\n"
        "CGPA: 9.2"
    )

    write_pdf(SAMPLES_DIR / f"{ROLL_NO}_resume.pdf", "Resume", resume_text)
    write_pdf(SAMPLES_DIR / f"{ROLL_NO}_resume1.pdf", "Resume (Alternate)", resume1_text)
    write_pdf(SAMPLES_DIR / f"{ROLL_NO}_marksheet.pdf", "Marksheet", marksheet_text)
    print(f"Sample PDFs written to {SAMPLES_DIR}")


if __name__ == "__main__":
    main()
