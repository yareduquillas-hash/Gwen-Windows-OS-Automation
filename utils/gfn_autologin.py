from __future__ import annotations

import io
import logging
import os
import time
from pathlib import Path
from typing import Callable

from utils.gfn_profiles import GameProfile, GFNProfileManager

log = logging.getLogger("jarvis.gfn.autologin")


class GFNAutoLogin:
    """Motor de detección visual y ejecución de inicio de sesión automatizado."""

    def __init__(self, profile_manager: GFNProfileManager | None = None):
        self.profile_mgr = profile_manager or GFNProfileManager()

    @staticmethod
    def _focus_gfn_window() -> bool:
        """Trae al frente y enfoca la ventana de GeForce NOW."""
        try:
            import pygetwindow as gw
            windows = [w for w in gw.getAllWindows() if "geforce now" in w.title.lower()]
            if not windows:
                return False
            win = windows[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.5)
            return True
        except Exception as exc:
            log.warning("No se pudo enfocar ventana GFN: %s", exc)
            return False

    def detect_login_screen(
        self,
        template_path: str,
        threshold: float = 0.82,
    ) -> bool:
        """Determina si la pantalla de login del juego coincide con la plantilla visual."""
        if not template_path or not os.path.isfile(template_path):
            # Si no hay plantilla configurada, asumimos que está listo tras el tiempo de carga
            return True

        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
        except Exception as exc:
            log.warning("Error capturando pantalla para template matching: %s", exc)
            return False

        try:
            # Intento 1: OpenCV (Template Matching preciso)
            import cv2
            import numpy as np
            from PIL import Image

            img_screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            img_template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

            if img_template is None:
                return False

            res = cv2.matchTemplate(img_screen, img_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            log.debug("Similitud de plantilla GFN: %.2f (umbral %.2f)", max_val, threshold)
            return bool(max_val >= threshold)

        except ImportError:
            # Fallback sin OpenCV: Similitud básica con Pillow
            try:
                from PIL import Image, ImageChops, ImageStat
                tmpl = Image.open(template_path).convert("L")
                sc = screenshot.convert("L").resize(tmpl.size)
                diff = ImageChops.difference(tmpl, sc)
                stat = ImageStat.Stat(diff)
                diff_val = stat.mean[0]
                # Menor diferencia implica mayor similitud
                return bool(diff_val < 45.0)
            except Exception as exc:
                log.warning("Error en fallback de comparación de imagen: %s", exc)
                return True

    def wait_and_autologin(
        self,
        profile: GameProfile,
        chat_id: int | None,
        bot: Any,
        status_cb: Callable[[str], None] | None = None,
        max_wait_seconds: int = 120,
        poll_interval: float = 2.0,
    ) -> bool:
        """Espera a que cargue la pantalla de autenticación y ejecuta el autologin."""
        def _notify(msg: str):
            if status_cb:
                status_cb(msg)
            elif bot and chat_id:
                try:
                    bot.send_message(chat_id, msg)
                except Exception:
                    pass

        _notify(f"⏳ *Cargando {profile.game_name}...* Esperando pantalla de inicio de sesión.")
        start_time = time.time()
        screen_ready = False

        while time.time() - start_time < max_wait_seconds:
            if profile.template_image and os.path.isfile(profile.template_image):
                if self.detect_login_screen(profile.template_image):
                    screen_ready = True
                    break
            else:
                # Sin plantilla: esperar 6 segundos para estabilización
                if time.time() - start_time >= 6.0:
                    screen_ready = True
                    break
            time.sleep(poll_interval)

        if not screen_ready:
            _notify(f"⚠️ Tiempo de espera agotado buscando la pantalla de login de *{profile.game_name}*.")
            return False

        _notify(f"🟢 *Listo.* Rellenando credenciales para *{profile.profile_name}* ({profile.account_email})...")
        return self.execute_autofill(profile, _notify)

    def execute_autofill(
        self,
        profile: GameProfile,
        notify_fn: Callable[[str], None] | None = None,
    ) -> bool:
        """Ejecuta la secuencia de pegado de credenciales con higiene total de portapapeles."""
        import pyautogui
        import pyperclip

        self._focus_gfn_window()
        time.sleep(0.8)

        # Si hay coordenadas específicas de clic para el primer campo
        if profile.click_coords:
            try:
                x, y = profile.click_coords
                pyautogui.click(x, y)
                time.sleep(0.3)
            except Exception as exc:
                log.warning("No se pudo hacer clic en coordenadas (%s): %s", profile.click_coords, exc)

        password_plain = profile.get_password()
        email = profile.account_email

        try:
            tokens = [t.strip().upper() for t in profile.key_sequence.split(",") if t.strip()]
            for token in tokens:
                if token == "EMAIL":
                    if email:
                        pyperclip.copy(email)
                        pyautogui.hotkey("ctrl", "v")
                        pyperclip.copy("")  # Limpieza inmediata
                        time.sleep(0.4)
                elif token == "TAB":
                    pyautogui.press("tab")
                    time.sleep(0.3)
                elif token == "PASSWORD":
                    if password_plain:
                        pyperclip.copy(password_plain)
                        pyautogui.hotkey("ctrl", "v")
                        pyperclip.copy("")  # Limpieza inmediata del portapapeles
                        time.sleep(0.4)
                elif token == "ENTER":
                    pyautogui.press("enter")
                    time.sleep(0.5)
                elif token.startswith("SLEEP"):
                    # Ejemplo: SLEEP_2 -> pausa 2 seg
                    try:
                        seconds = float(token.split("_")[-1])
                        time.sleep(seconds)
                    except Exception:
                        time.sleep(1.0)
                else:
                    pyautogui.press(token.lower())
                    time.sleep(0.2)

            log.info("Autofill completado exitosamente para %s (%s)", profile.game_name, profile.profile_name)
            if notify_fn:
                notify_fn(f"✅ *Sesión iniciada con éxito* para *{profile.game_name}* con la cuenta *{profile.profile_name}*.")
            return True

        except Exception as exc:
            log.error("Error durante autofill de GFN: %s", exc)
            if notify_fn:
                notify_fn(f"❌ Error durante el inicio de sesión automático: {exc}")
            return False
        finally:
            # Garantía absoluta de portapapeles limpio
            try:
                pyperclip.copy("")
            except Exception:
                pass
