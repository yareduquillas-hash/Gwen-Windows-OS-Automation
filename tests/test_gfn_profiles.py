from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from utils.gfn_profiles import (
    GFNProfileManager,
    GameProfile,
    _decrypt_dpapi,
    _encrypt_dpapi,
)
from utils.gfn_autologin import GFNAutoLogin


class GFNProfilesTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        # Reset singleton instance for isolated test
        GFNProfileManager._instance = None
        self.mgr = GFNProfileManager(storage_path=self.test_dir)

    def tearDown(self):
        GFNProfileManager._instance = None
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dpapi_encryption_roundtrip(self):
        secret = "MiClaveSuperSegura123!_Gmail"
        encrypted = _encrypt_dpapi(secret)
        self.assertNotEqual(secret, encrypted)
        self.assertTrue(len(encrypted) > 0)

        decrypted = _decrypt_dpapi(encrypted)
        self.assertEqual(secret, decrypted)

    def test_profile_crud_operations(self):
        # Crear perfil
        prof = self.mgr.create_or_update_profile(
            game_name="Genshin Impact",
            profile_name="Principal Gmail",
            account_email="usuario@gmail.com",
            password_plain="Password12345",
            key_sequence="EMAIL,TAB,PASSWORD,ENTER",
        )
        self.assertIsNotNone(prof.id)
        self.assertEqual(prof.game_name, "Genshin Impact")

        # Recuperar perfil
        fetched = self.mgr.get_profile(prof.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.account_email, "usuario@gmail.com")
        self.assertEqual(fetched.get_password(), "Password12345")

        # Buscar por juego
        found = self.mgr.find_profile_for_game("Genshin", "Principal")
        self.assertIsNotNone(found)
        self.assertEqual(found.id, prof.id)

        # Listar perfiles
        profs = self.mgr.list_profiles()
        self.assertEqual(len(profs), 1)

        # Eliminar perfil
        deleted = self.mgr.delete_profile(prof.id)
        self.assertTrue(deleted)
        self.assertIsNone(self.mgr.get_profile(prof.id))

    def test_public_dict_does_not_expose_password(self):
        prof = self.mgr.create_or_update_profile(
            game_name="Fortnite",
            profile_name="Cuenta Epic",
            account_email="gamer@epicgames.com",
            password_plain="FortniteEpicSecret!",
        )
        public_data = prof.to_public_dict()
        self.assertNotIn("password", public_data)
        self.assertNotIn("password_encrypted", public_data)
        self.assertTrue(public_data["has_password"])
        self.assertEqual(public_data["game_name"], "Fortnite")

    @patch("pyautogui.click")
    @patch("pyautogui.hotkey")
    @patch("pyautogui.press")
    @patch("pygetwindow.getAllWindows", return_value=[])
    def test_clipboard_hygiene_on_autofill(self, mock_gw, mock_press, mock_hotkey, mock_click):
        import pyperclip

        prof = self.mgr.create_or_update_profile(
            game_name="Honkai",
            profile_name="Main",
            account_email="honkai@gmail.com",
            password_plain="HonkaiSecret123",
        )

        autologin = GFNAutoLogin(self.mgr)
        success = autologin.execute_autofill(prof)
        self.assertTrue(success)

        # El portapapeles final debe estar completamente vacío
        self.assertEqual(pyperclip.paste(), "")


if __name__ == "__main__":
    unittest.main()
