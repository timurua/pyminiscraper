from typing import Optional
import base64
import uuid
import hashlib
from pathlib import Path
import mimetypes

def generate_url_safe_uuid() -> str:
    uuid_bytes = uuid.uuid4().bytes
    url_safe_id = base64.urlsafe_b64encode(uuid_bytes).rstrip(b'=').decode('utf-8')
    return url_safe_id

def generate_url_safe_id(input_string:str)->str:
    sha256_hash = hashlib.sha256(input_string.encode())
    base64_encoded = base64.urlsafe_b64encode(sha256_hash.digest()).decode('utf-8')
    return base64_encoded[:32]

def generate_url_safe_hash_for_file(file_path)->str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    base64_encoded = base64.urlsafe_b64encode(sha256_hash.digest()).decode('utf-8')
    return base64_encoded[:32]