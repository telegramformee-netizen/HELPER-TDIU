"""
crypto.py — AES-256-GCM shifrlash/deshifrlash
Hemis parollari xavfsiz saqlanadi
"""
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import config

_KEY = config.AES_KEY.encode()[:32]  # 32 bayt


def encrypt(text: str) -> str:
    nonce = get_random_bytes(16)
    cipher = AES.new(_KEY, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(text.encode())
    return base64.b64encode(nonce + tag + ciphertext).decode()


def decrypt(token: str) -> str:
    data = base64.b64decode(token)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(_KEY, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()
