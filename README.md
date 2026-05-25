# Secure Document Verification System

A small Python project that lets a **recruiter** check whether a candidate’s resume and marksheet are **real** or **fake** — without calling the college on the phone every time.

This README assumes you are new to programming. Technical terms are explained as we go.

---

## The problem this solves

When someone applies for a job, they might send:

- A resume (PDF)
- A marksheet (PDF)

Sometimes people **edit** those files to look better than they really are. Colleges can verify the truth, but that is slow (emails, phone calls, waiting).

This project automates verification:

1. The **institute** reads the real PDFs and stores a secure “fingerprint” (hash) of the text.
2. The **candidate** shares their documents with the recruiter inside a **QR code**.
3. The **recruiter** scans the QR, rebuilds the fingerprint, and compares it to what the institute stored.

If the fingerprints match → documents are authentic.  
If they do not match → someone changed the data.

---

## The four parts (who does what?)

Think of four separate programs that talk to each other over the network (like four people on a phone call):

| Part | File | Port | Simple role |
|------|------|------|-------------|
| **Central Server** | `centralServer.py` | 8000 | Keeps the official fingerprint for each student roll number |
| **Institute** | `institute.py` | 8001 | Reads PDFs, creates the fingerprint, saves it on the Central Server |
| **Candidate** | `candidate.py` | (client) | Gets document text, makes a QR code, sends it to the recruiter |
| **Recruiter** | `recruiter.py` | 8002 | Receives the QR, checks if it matches the official fingerprint |

```
Candidate  →  Institute     (get document text)
Institute  →  Central Server (store official hash)
Candidate  →  Recruiter      (send QR code + roll number)
Recruiter  →  Central Server (fetch official hash)
Recruiter  →  compares hashes → SUCCESS or FAILED
```

---

## Key ideas (beginner-friendly)

### Hash (fingerprint)

A **hash** turns any text into a short fixed code. If even one letter in the document changes, the hash changes completely.

We use **SHA-256** (via Python’s `hashlib`).

### QR code

A **QR code** is a square barcode your phone can scan. Here it holds the candidate’s document text (compressed so it fits).

### RSA encryption

When the institute sends a hash to the Central Server, and when the recruiter fetches it, the data is **encrypted** with RSA keys (files in the `keys/` folder). That way only the right party can read it.

You do not need to understand the math — just know: **keys = locks and keys for secure messages**.

### PDF extraction

`pdfplumber` reads text out of PDF files. The institute reads:

- `{roll_number}_resume.pdf`
- `{roll_number}_marksheet.pdf`

from the `samples/` folder.

---

## What you need installed

1. **Python 3.10+** — [python.org](https://www.python.org/downloads/)  
   During install on Windows, check **“Add Python to PATH”**.

2. **pip** — usually comes with Python (installs libraries).

3. **Project libraries** — installed with one command (see below).

### Windows note (QR scanning)

The recruiter uses `pyzbar` to read QR images. On Windows you may need the **ZBar** library. If QR decoding fails, search for “pyzbar Windows install” or install ZBar and add it to your PATH.

---

## Quick start (easiest way)

Open **PowerShell** or **Command Prompt** in this project folder, then run:

```powershell
cd "c:\Users\dheer\OneDrive\Desktop\Authentication Porject"
python -m pip install -r requirements.txt
python run_demo.py
```

`run_demo.py` will:

1. Create RSA keys (if missing) in `keys/`
2. Create sample PDFs (if missing) in `samples/`
3. Start the Central Server and Institute in the background
4. Run two tests:
   - **Authentic** — candidate sends real data → **Verification Successful**
   - **Tampered** — candidate swaps in a fake resume → **Verification Failed**

If you see **“All end-to-end demos passed.”**, everything works.

---

## Manual run (four terminals)

Use this to see each part step by step. Open **four** terminal windows in the project folder.

**Terminal 1 — Central Server**

```powershell
python centralServer.py
```

**Terminal 2 — Institute**

```powershell
python institute.py
```

**Terminal 3 — Recruiter**

```powershell
python recruiter.py
```

**Terminal 4 — Candidate**

```powershell
python candidate.py
```

When prompted:

- **Roll number:** `22CSB0F23` (sample student included in the project)
- **Forward data now?**  
  - `y` = send the real documents from the institute  
  - `n` = replace resume with a different PDF (`22CSB0F23_resume1.pdf`) to simulate tampering

Watch Terminal 3 for the verification result.

---

## Project folder guide

```
Authentication Porject/
├── centralServer.py      # Stores and serves hashes
├── institute.py          # Reads PDFs, sends hash to central server
├── candidate.py          # Builds QR, sends to recruiter
├── recruiter.py          # Verifies QR against central server
├── utils.py              # Shared helpers (PDF, hash, sockets)
├── generate_keys.py      # Creates RSA keys in keys/
├── generate_sample_pdfs.py  # Creates test PDFs in samples/
├── run_demo.py           # Runs full demo automatically
├── requirements.txt      # Python packages to install
├── keys/                 # RSA public/private keys (generated)
└── samples/              # Test resume & marksheet PDFs
```

### Files created when you run the app

| File | Meaning |
|------|---------|
| `compressed_qr.png` | QR code the candidate generated |
| `received_qr.png` | QR code the recruiter received |
| `insti_file.txt` | Text the institute extracted |
| `candi_file.txt` | Text the candidate put in the QR |
| `rec_file.txt` | Text the recruiter decoded from the QR |

---

## Sample test student

| Item | Value |
|------|--------|
| Roll number | `22CSB0F23` |
| Real resume | `samples/22CSB0F23_resume.pdf` |
| Fake resume (tamper test) | `samples/22CSB0F23_resume1.pdf` |
| Marksheet | `samples/22CSB0F23_marksheet.pdf` |

To add your own student, put PDFs in `samples/` named like `ROLLNO_resume.pdf` and `ROLLNO_marksheet.pdf`, then use that roll number when running `candidate.py`.

---

## Regenerating keys or sample PDFs

```powershell
python generate_keys.py
python generate_sample_pdfs.py
```

**Warning:** If you regenerate keys after hashes were stored, old stored hashes will no longer decrypt correctly. For a fresh start, restart the Central Server (it keeps hashes in memory only).

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `ConnectionRefusedError` on port 8001 or 8002 | Start servers in order: Central Server → Institute → Recruiter, then run Candidate |
| `No module named ...` | Run `python -m pip install -r requirements.txt` |
| QR decode fails | Install ZBar for Windows; ensure `pyzbar` is installed |
| Port already in use | Close old Python windows or restart the computer |
| Verification always fails | Use roll number `22CSB0F23` and answer `y` for authentic test; ensure Institute ran before Candidate |

---

## How security works (short version)

1. **Integrity** — SHA-256 hash detects any change in document text.
2. **Storage** — Hash is encrypted before sent to the Central Server.
3. **Retrieval** — Recruiter receives hash encrypted for them only.
4. **Sharing** — Document text travels in a QR code from candidate to recruiter.

This is a **learning / demo** project. A production system would also use HTTPS, a real database, login, and more — but the core idea is the same.

---


