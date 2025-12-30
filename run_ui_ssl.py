from __future__ import annotations

import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from python.helpers.files import get_abs_path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def tmp_cert_dir() -> Path:
    d = Path(get_abs_path("tmp"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_dev_ca_and_server_cert(tmp_dir: Path) -> dict[str, Path]:
    """
    Generates:
      - tmp/ca.key.pem, tmp/ca.pem
      - tmp/server.key.pem, tmp/server.pem, tmp/server.fullchain.pem
    Skips generation if all files exist.
    """
    ca_key_path = tmp_dir / "ca.key.pem"
    ca_cert_path = tmp_dir / "ca.pem"

    srv_key_path = tmp_dir / "server.key.pem"
    srv_cert_path = tmp_dir / "server.pem"
    srv_fullchain_path = tmp_dir / "server.fullchain.pem"

    required = [
        ca_key_path,
        ca_cert_path,
        srv_key_path,
        srv_cert_path,
        srv_fullchain_path,
    ]
    if all(p.exists() for p in required):
        return {
            "ca_key": ca_key_path,
            "ca_cert": ca_cert_path,
            "server_key": srv_key_path,
            "server_cert": srv_cert_path,
            "server_fullchain": srv_fullchain_path,
        }

    now = datetime.now(timezone.utc)
    not_before = now - timedelta(days=1)

    # --- CA key + cert ---
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Agent Zero"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Agent Zero Root CA"),
        ]
    )

    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_subject)
        .issuer_name(ca_subject)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key=ca_key, algorithm=hashes.SHA256())
    )

    ca_key_path.write_bytes(
        ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    ca_cert_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))

    # --- Server key + cert (signed by CA) ---
    srv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    srv_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])

    san = x509.SubjectAlternativeName(
        [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            x509.IPAddress(ipaddress.ip_address("::1")),
        ]
    )

    srv_cert = (
        x509.CertificateBuilder()
        .subject_name(srv_subject)
        .issuer_name(ca_subject)
        .public_key(srv_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(now + timedelta(days=825))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(san, critical=False)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key=ca_key, algorithm=hashes.SHA256())
    )

    srv_key_path.write_bytes(
        srv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    srv_cert_path.write_bytes(srv_cert.public_bytes(serialization.Encoding.PEM))

    # Fullchain = leaf + CA
    srv_fullchain_path.write_bytes(
        srv_cert.public_bytes(serialization.Encoding.PEM) + ca_cert.public_bytes(serialization.Encoding.PEM)
    )

    return {
        "ca_key": ca_key_path,
        "ca_cert": ca_cert_path,
        "server_key": srv_key_path,
        "server_cert": srv_cert_path,
        "server_fullchain": srv_fullchain_path,
    }
