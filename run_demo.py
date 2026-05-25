import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ROLL_NO = "22CSB0F23"
PYTHON = sys.executable


def run_script(name: str) -> None:
    subprocess.run([PYTHON, str(PROJECT_ROOT / name)], cwd=PROJECT_ROOT, check=True)


def wait_for_servers(cs_proc: subprocess.Popen, inst_proc: subprocess.Popen, timeout: float = 15.0) -> bool:
    import socket

    deadline = time.time() + timeout
    while time.time() < deadline:
        if cs_proc.poll() is not None or inst_proc.poll() is not None:
            return False
        try:
            with socket.create_connection(("localhost", 8000), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def start_server(script: str) -> subprocess.Popen:
    return subprocess.Popen(
        [PYTHON, "-u", str(PROJECT_ROOT / script)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_verification_demo(forward_authentic: bool) -> bool:
    log_file = PROJECT_ROOT / "recruiter_demo.log"
    with open(log_file, "w", encoding="utf-8") as log:
        recruiter = subprocess.Popen(
            [PYTHON, "-u", str(PROJECT_ROOT / "recruiter.py")],
            cwd=PROJECT_ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

    time.sleep(1.0)

    flag = "y" if forward_authentic else "n"
    candidate = subprocess.run(
        [PYTHON, str(PROJECT_ROOT / "candidate.py"), ROLL_NO, flag],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if candidate.returncode != 0:
        print(candidate.stdout)
        print(candidate.stderr, file=sys.stderr)
        recruiter.kill()
        recruiter.wait()
        return False

    recruiter.wait(timeout=30)
    output = log_file.read_text(encoding="utf-8")
    print(output)

    if forward_authentic:
        return "Verification Successful" in output
    return "Verification Failed" in output


def main() -> None:
    if not (PROJECT_ROOT / "keys" / "cs_public.pem").exists():
        print("Generating RSA keys...")
        run_script("generate_keys.py")

    if not (PROJECT_ROOT / "samples" / f"{ROLL_NO}_resume.pdf").exists():
        print("Generating sample PDFs...")
        run_script("generate_sample_pdfs.py")

    print("Installing dependencies...")
    subprocess.run(
        [PYTHON, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements.txt")],
        cwd=PROJECT_ROOT,
        check=True,
    )

    cs_proc = start_server("centralServer.py")
    inst_proc = start_server("institute.py")
    time.sleep(2)

    if not wait_for_servers(cs_proc, inst_proc, timeout=15.0):
        print("Servers failed to start (central server or institute exited)", file=sys.stderr)
        cs_proc.kill()
        inst_proc.kill()
        raise SystemExit(1)

    print("\n=== Demo A: Authentic documents ===")
    authentic_ok = run_verification_demo(forward_authentic=True)
    print(f"Authentic demo: {'PASSED' if authentic_ok else 'FAILED'}")

    print("\n=== Demo B: Tampered documents ===")
    tamper_ok = run_verification_demo(forward_authentic=False)
    print(f"Tamper demo: {'PASSED' if tamper_ok else 'FAILED'}")

    cs_proc.kill()
    inst_proc.kill()
    cs_proc.wait()
    inst_proc.wait()

    if authentic_ok and tamper_ok:
        print("\nAll end-to-end demos passed.")
        return

    print("\nOne or more demos failed.", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
