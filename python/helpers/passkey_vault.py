import json

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticationCredential,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    RegistrationCredential,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)


class PasskeyVaultManager:
    """Manages Passkey registration and verification for centralized auth."""

    RP_NAME = "Agent Jumbo Central"

    def __init__(self, db):
        self.db = db

    def get_registration_options(self, user_id: str, username: str, rp_id: str):
        """Generate options for registering a new passkey. Enforces hardware requirements if enabled."""
        from python.helpers.security import SecurityManager

        # Hardware Enclave Attestation logic
        auth_selection = None
        attestation = "none"

        if SecurityManager.STRICT_HARDWARE_ONLY:
            # Require a platform authenticator (TouchID, FaceID, Windows Hello, Android Biometrics)
            auth_selection = AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                resident_key=ResidentKeyRequirement.REQUIRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            )
            attestation = "direct"  # Request attestation data for hardware verification
            print("[🛡️ Security] Enforcing Strict Hardware Attestation for Passkey registration.")

        options = generate_registration_options(
            rp_id=rp_id,
            rp_name=self.RP_NAME,
            user_id=user_id,
            user_name=username,
            attestation=attestation,
            authenticator_selection=auth_selection,
        )
        return json.loads(options_to_json(options))

    def verify_registration(self, user_id: str, challenge: str, response_data: dict, rp_id: str, origin: str):
        """Verify the registration response from the phone."""
        try:
            credential = RegistrationCredential.parse_obj(response_data)
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=challenge,
                expected_origin=origin,
                expected_rp_id=rp_id,
            )

            # Save to DB
            self._save_passkey(
                user_id=user_id,
                passkey_id=verification.credential_id,
                public_key=verification.public_key,
                sign_count=verification.sign_count,
            )
            return {
                "success": True,
                "credential_id": verification.credential_id.decode("utf-8")
                if isinstance(verification.credential_id, bytes)
                else str(verification.credential_id),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_authentication_options(self, user_id: str, rp_id: str):
        """Generate options for authenticating with a registered passkey."""
        passkeys = self._get_user_passkeys(user_id)
        if not passkeys:
            return {"error": "No passkeys registered for this user."}

        options = generate_authentication_options(
            rp_id=rp_id,
            allow_credentials=[{"id": p["passkey_id"], "type": "public-key"} for p in passkeys],
        )
        return json.loads(options_to_json(options))

    def verify_authentication(self, user_id: str, challenge: str, response_data: dict, rp_id: str, origin: str):
        """Verify the authentication signature from the phone."""
        try:
            credential = AuthenticationCredential.parse_obj(response_data)
            passkey = self._get_passkey(credential.id)
            if not passkey:
                return {"success": False, "error": "Passkey not found"}

            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=challenge,
                expected_origin=origin,
                expected_rp_id=rp_id,
                credential_public_key=passkey["public_key"],
                credential_current_sign_count=passkey["sign_count"],
            )

            # Update sign count
            self._update_sign_count(credential.id, verification.new_sign_count)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # DB Helpers
    def _save_passkey(self, user_id, passkey_id, public_key, sign_count):
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_passkeys (passkey_id, user_id, public_key, sign_count)
            VALUES (?, ?, ?, ?)
        """,
            (passkey_id, user_id, public_key, sign_count),
        )
        conn.commit()
        conn.close()

    def _get_user_passkeys(self, user_id):
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_passkeys WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _get_passkey(self, passkey_id):
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_passkeys WHERE passkey_id = ?", (passkey_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def _update_sign_count(self, passkey_id, sign_count):
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_passkeys SET sign_count = ?, last_used = CURRENT_TIMESTAMP WHERE passkey_id = ?",
            (sign_count, passkey_id),
        )
        conn.commit()
        conn.close()
