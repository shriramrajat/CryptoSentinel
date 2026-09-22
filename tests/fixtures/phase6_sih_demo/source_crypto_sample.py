"""SIH demo sample: Python source with representative cryptographic usage."""
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
import hashlib

# RSA key generation
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# ECDSA signing key
ec_key = ec.generate_private_key(ec.SECP256R1())

# AES-256-GCM
cipher = Cipher(algorithms.AES(b"\x00" * 32), modes.GCM(b"\x00" * 12))

# SHA-1 (weak)
h = hashlib.sha1(b"data").hexdigest()

# SHA-256
h2 = hashlib.sha256(b"data").hexdigest()
