from __future__ import annotations

import logging
import os
import subprocess
import time as _time
from pathlib import Path
from typing import Any

from .base import PlatformAdapter

log = logging.getLogger("jarvis.platform.win")


class WindowsAdapter(PlatformAdapter):
    @staticmethod
    def _speaker_endpoint_volume():
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        if devices is None:
            return None

        try:
            endpoint = getattr(devices, "EndpointVolume", None)
        except Exception:
            endpoint = None
        if endpoint is not None:
            return endpoint

        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    def get_battery(self) -> dict[str, str]:
        try:
            import subprocess
            r = subprocess.run(
                [
                    "powershell", "-Command",
                    "Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json",
                ],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode != 0:
                return {"error": "No disponible"}
            import json
            data = json.loads(r.stdout.strip())
            pct = data.get("EstimatedChargeRemaining", "?")
            status_map = {1: "Descargando", 2: "Conectado", 3: "Cargando", 4: "Crítico"}
            status = status_map.get(data.get("BatteryStatus", 0), "Desconocido")
            return {"percentage": str(pct), "state": status}
        except Exception as exc:
            return {"error": str(exc)}

    def get_system_info(self) -> dict[str, Any]:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_total_gb": round(psutil.disk_usage("C:\\").total / (1024**3), 1),
            "disk_free_gb": round(psutil.disk_usage("C:\\").free / (1024**3), 1),
            "disk_percent": psutil.disk_usage("C:\\").percent,
            "boot_time": psutil.boot_time(),
        }

    def set_volume(self, level: int) -> bool:
        level = max(0, min(100, level))
        try:
            volume = self._speaker_endpoint_volume()
            if volume is None:
                return False
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return True
        except Exception as exc:
            log.warning("set_volume falló: %s", exc)
            return False

    def get_volume(self) -> int:
        try:
            volume = self._speaker_endpoint_volume()
            if volume is None:
                return -1
            return round(volume.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            return -1

    def send_media_key(self, key: str) -> bool:
        import pyautogui
        key_map = {
            "play_pause": "playpause",
            "pause": "playpause",
            "play": "playpause",
            "next": "nexttrack",
            "prev": "prevtrack",
            "previous": "prevtrack",
            "stop": "stop",
        }
        vk = key_map.get(key.lower())
        if not vk:
            return False
        pyautogui.press(vk)
        return True

    def copy_to_clipboard(self, text: str) -> bool:
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    def take_screenshot(self) -> bytes | None:
        try:
            import pyautogui
            import io
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as exc:
            log.warning("take_screenshot falló: %s", exc)
            return None

    def lock_screen(self) -> bool:
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return True
        except Exception:
            return False

    def shutdown(self) -> bool:
        try:
            subprocess.run(["shutdown", "/s", "/t", "5"], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def reboot(self) -> bool:
        try:
            subprocess.run(["shutdown", "/r", "/t", "5"], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def get_shell(self) -> str:
        return "powershell.exe"

    def install_package(self, name: str) -> bool:
        try:
            kw = {}
            if os.name == "nt":
                kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            r = subprocess.run(
                ["winget", "install", "-e", "--id", name, "--accept-source-agreements"],
                capture_output=True, text=True, timeout=120, **kw
            )
            return r.returncode == 0
        except Exception:
            return False

    def get_running_processes(self, top_n: int = 10) -> list[dict]:
        import psutil
        procs = []
        for p in psutil.process_iter(["name", "memory_info", "cpu_percent"]):
            try:
                info = p.info
                procs.append({
                    "name": info["name"] or "",
                    "memory_mb": round(info["memory_info"].rss / (1024 * 1024), 1) if info["memory_info"] else 0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x["memory_mb"], reverse=True)
        return procs[:top_n]

    def kill_process(self, name: str) -> bool:
        import psutil
        requested = name.strip().lower().removesuffix(".exe")
        protected = {"system", "system idle process", "smss", "csrss", "wininit", "services", "lsass", "winlogon"}
        matches = []
        for p in psutil.process_iter(["name"]):
            try:
                process_name = (p.info["name"] or "").lower()
                process_stem = process_name.removesuffix(".exe")
                if (
                    process_stem == requested
                    and process_stem not in protected
                    and p.pid != psutil.Process().pid
                ):
                    matches.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not matches:
            return False
        killed_any = False
        for proc in matches:
            try:
                proc.kill()
                killed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return killed_any

    def get_windows(self) -> list[str]:
        try:
            import pygetwindow as gw
            return [w.title for w in gw.getAllWindows() if w.title.strip()]
        except Exception:
            return []

    def focus_window(self, title: str) -> bool:
        try:
            import pygetwindow as gw
            matches = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
            if not matches:
                return False
            win = matches[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            return True
        except Exception:
            return False

    def minimize_all(self) -> bool:
        try:
            import pyautogui
            pyautogui.hotkey("win", "d")
            return True
        except Exception:
            return False

    def send_notification(self, title: str, message: str) -> bool:
        try:
            from win10toast import ToastNotifier
            toast = ToastNotifier()
            toast.show_toast(title, message, duration=5, threaded=True)
            return True
        except Exception:
            return False

    def open_url(self, url: str) -> bool:
        import webbrowser
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False
