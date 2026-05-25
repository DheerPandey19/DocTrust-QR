from pathlib import Path

from Crypto.PublicKey import RSA

from utils import KEYS_DIR


def generate_key_pair(name: str) -> None:
    key = RSA.generate(2048)
    private_pem = key.export_key()
    public_pem = key.publickey().export_key()

    (KEYS_DIR / f"{name}_private.pem").write_bytes(private_pem)
    (KEYS_DIR / f"{name}_public.pem").write_bytes(public_pem)
    print(f"Generated {name}_private.pem and {name}_public.pem")


def main() -> None:
    KEYS_DIR.mkdir(exist_ok=True)
    generate_key_pair("cs")
    generate_key_pair("r")
    print(f"Keys written to {KEYS_DIR}")


if __name__ == "__main__":
    main()
