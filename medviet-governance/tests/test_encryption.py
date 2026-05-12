import pytest
import os
from src.encryption.vault import SimpleVault


class TestEncryption:
    """Test envelope encryption (KEK → DEK → Data)"""

    @pytest.fixture
    def vault(self):
        """Create fresh vault for each test"""
        vault = SimpleVault(master_key_path=".vault_test_key")
        yield vault
        # Cleanup
        if os.path.exists(".vault_test_key"):
            os.remove(".vault_test_key")

    def test_kek_creation(self, vault):
        """Test KEK is created and persisted"""
        assert vault.kek is not None
        assert len(vault.kek) == 32  # 256-bit
        assert os.path.exists(".vault_test_key")

    def test_kek_persistence(self, vault):
        """Test KEK is loaded from file on second instance"""
        kek1 = vault.kek
        vault2 = SimpleVault(master_key_path=".vault_test_key")
        kek2 = vault2.kek
        assert kek1 == kek2

    def test_dek_generation(self, vault):
        """Test DEK generation and encryption"""
        plaintext_dek, encrypted_dek = vault.generate_dek()
        assert plaintext_dek is not None
        assert encrypted_dek is not None
        assert len(plaintext_dek) == 32
        assert len(encrypted_dek) > 32  # Contains nonce + ciphertext

    def test_encrypt_decrypt_dek(self, vault):
        """Test DEK encryption/decryption round-trip"""
        plaintext_dek, encrypted_dek = vault.generate_dek()
        decrypted_dek = vault.decrypt_dek(encrypted_dek)
        assert plaintext_dek == decrypted_dek

    def test_encrypt_data(self, vault):
        """Test data encryption returns correct format"""
        text = "Bệnh nhân: Nguyễn Văn A, CCCD: 123456789012"
        payload = vault.encrypt_data(text)
        
        assert isinstance(payload, dict)
        assert "encrypted_dek" in payload
        assert "ciphertext" in payload
        assert "algorithm" in payload
        assert payload["algorithm"] == "AES-256-GCM"
        
        # Should be base64 encoded
        import base64
        base64.b64decode(payload["encrypted_dek"])
        base64.b64decode(payload["ciphertext"])

    def test_encrypt_decrypt_roundtrip(self, vault):
        """Test full round-trip encryption/decryption"""
        original_text = "Bệnh nhân: Nguyễn Văn A, CCCD: 123456789012, Điện thoại: 0912345678"
        
        # Encrypt
        payload = vault.encrypt_data(original_text)
        
        # Decrypt
        decrypted_text = vault.decrypt_data(payload)
        
        assert decrypted_text == original_text

    def test_encrypt_multiple_different_values(self, vault):
        """Test encrypting different values produces different ciphertexts"""
        text1 = "Value 1"
        text2 = "Value 2"
        
        payload1 = vault.encrypt_data(text1)
        payload2 = vault.encrypt_data(text2)
        
        # Ciphertexts should be different
        assert payload1["ciphertext"] != payload2["ciphertext"]
        
        # But decryption should work for both
        assert vault.decrypt_data(payload1) == text1
        assert vault.decrypt_data(payload2) == text2

    def test_decrypt_invalid_payload_fails(self, vault):
        """Test decryption with invalid payload raises error"""
        invalid_payload = {
            "encrypted_dek": "invalid_base64!@#",
            "ciphertext": "invalid_base64!@#",
            "algorithm": "AES-256-GCM"
        }
        
        with pytest.raises(Exception):
            vault.decrypt_data(invalid_payload)


class TestVaultIntegration:
    """Test vault integration with dataframe encryption"""

    @pytest.fixture
    def vault(self):
        vault = SimpleVault(master_key_path=".vault_integration_test")
        yield vault
        if os.path.exists(".vault_integration_test"):
            os.remove(".vault_integration_test")

    def test_encrypt_column(self, vault):
        """Test encrypting a dataframe column"""
        import pandas as pd
        
        df = pd.DataFrame({
            "patient_id": ["P001", "P002", "P003"],
            "cccd": ["123456789012", "234567890123", "345678901234"],
            "name": ["Nguyễn Văn A", "Trần Thị B", "Phạm Văn C"]
        })
        
        df_encrypted = df.copy()
        df_encrypted["cccd"] = df_encrypted["cccd"].apply(
            lambda x: vault.encrypt_data(str(x))
        )
        
        # Verify encryption happened
        assert all(isinstance(x, dict) for x in df_encrypted["cccd"])
        
        # Verify decryption works
        df_decrypted = df_encrypted.copy()
        df_decrypted["cccd"] = df_decrypted["cccd"].apply(
            lambda x: vault.decrypt_data(x)
        )
        
        assert list(df_decrypted["cccd"]) == list(df["cccd"])
