from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings


def _key_dir() -> Path:
	return Path(settings.BASE_DIR) / '.webpush'


def _private_key_path() -> Path:
	return _key_dir() / 'vapid_private.pem'


def _public_key_path() -> Path:
	return _key_dir() / 'vapid_public.txt'


def _generate_keypair() -> tuple[str, str]:
	private_key = ec.generate_private_key(ec.SECP256R1())
	private_key_der = private_key.private_bytes(
		encoding=serialization.Encoding.DER,
		format=serialization.PrivateFormat.PKCS8,
		encryption_algorithm=serialization.NoEncryption(),
	)
	private_key_b64 = base64.urlsafe_b64encode(private_key_der).decode('utf-8').rstrip('=')
	private_key_pem = private_key.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.PKCS8,
		encryption_algorithm=serialization.NoEncryption(),
	).decode('utf-8')
	public_key_bytes = private_key.public_key().public_bytes(
		encoding=serialization.Encoding.X962,
		format=serialization.PublicFormat.UncompressedPoint,
	)
	public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
	return private_key_b64, public_key_b64


def _ensure_keypair() -> tuple[str, str]:
	key_dir = _key_dir()
	key_dir.mkdir(parents=True, exist_ok=True)
	private_path = _private_key_path()
	public_path = _public_key_path()

	if private_path.exists() and public_path.exists():
		stored_private_key = private_path.read_text(encoding='utf-8').strip()
		stored_public_key = public_path.read_text(encoding='utf-8').strip()

		if stored_private_key.startswith('-----BEGIN'):
			loaded_private_key = serialization.load_pem_private_key(
				stored_private_key.encode('utf-8'),
				password=None,
			)
			private_key_der = loaded_private_key.private_bytes(
				encoding=serialization.Encoding.DER,
				format=serialization.PrivateFormat.PKCS8,
				encryption_algorithm=serialization.NoEncryption(),
			)
			stored_private_key = base64.urlsafe_b64encode(private_key_der).decode('utf-8').rstrip('=')
			private_path.write_text(stored_private_key, encoding='utf-8')

		return stored_private_key, stored_public_key

	private_key_b64, public_key_b64 = _generate_keypair()
	private_path.write_text(private_key_b64, encoding='utf-8')
	public_path.write_text(public_key_b64, encoding='utf-8')
	return private_key_b64, public_key_b64


def get_vapid_private_key_pem() -> str:
	private_key_b64, _ = _ensure_keypair()
	return private_key_b64


def get_vapid_public_key() -> str:
	_, public_key_b64 = _ensure_keypair()
	return public_key_b64


def get_vapid_claims() -> dict[str, str]:
	contact_email = getattr(settings, 'WEB_PUSH_CONTACT_EMAIL', 'admin@localhost')
	if contact_email.startswith('mailto:'):
		return {'sub': contact_email}
	return {'sub': f'mailto:{contact_email}'}