from __future__ import annotations

import logging
import subprocess
from typing import Any

from .base import PlatformAdapter

log = logging.getLogger("jarvis.platform.linux")


class LinuxAdapter(PlatformAdapter):
    def get_battery(self) -> dict[str, str]:
        try:
            r = subprocess.run(
                ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"],
                timeout=5, capture_output=True, text=True,
            )
            out = r.stdout
            if not out:
                r2 = subprocess.run(["upower", "-e"], timeout=5, capture_output=True, text=True)
                for line in r2.stdout.splitlines():
                    if "BAT" in line:
                        r = subprocess.run(["upower", "-i", line.strip()], timeout=5, capture_output=True, text=True)
                        out = r.stdout
                        break
            if not out:
                return {"error": "No disponible"}
            pct = ""
            state = ""
            for line in out.splitlines():
                l = line.strip()
                if l.startswith("percentage:"):
                    pct = l.split(":", 1)[1].strip()
                if l.startswith("state:"):
                    state = l.split(":", 1)[1].strip()
            return {"percentage": pct or "?", "state": state or "?"}
        except Exception as exc:
            return {"error": str(exc)}

    def get_system_info(self) -> dict[str, Any]:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_total_gb": round(psutil.disk_usage("/").total / (1024**3), 1),
            "disk_free_gb": round(psutil.disk_usage("/").free / (1024**3), 1),
            "disk_percent": psutil.disk_usage("/").percent,
            "boot_time": psutil.boot_time(),
        }

    def set_volume(self, level: int) -> bool:
        level = max(0, min(100, level))
        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                timeout=5, capture_output=True,
            )
            return True
        except Exception:
            return False

    def get_volume(self) -> int:
        try:
            r = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                timeout=5, capture_output=True, text=True,
            )
            for token in r.stdout.split():
                if token.endswith("%"):
                    return int(token.replace("%", ""))
            return -1
        except Exception:
            return -1

    def send_media_key(self, key: str) -> bool:
        cmd_map = {
            "play_pause": "PlayPause", "pause": "PlayPause", "play": "PlayPause",
            "next": "Next", "prev": "Previous", "previous": "Previous",
            "stop": "Stop",
        }
        cmd = cmd_map.get(key.lower())
        if not cmd:
            return False
        try:
            subprocess.run(["playerctl", "-a", cmd.lower()], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def copy_to_clipboard(self, text: str) -> bool:
        for tool in ["xclip -selection clipboard", "xsel -ib"]:
            try:
                p = subprocess.Popen(tool.split(), stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8"), timeout=5)
                if p.returncode == 0:
                    return True
            except Exception:
                continue
        return False

    def take_screenshot(self) -> bytes | None:
        try:
            import io
            import subprocess
            r = subprocess.run(["scrot", "-"], capture_output=True, timeout=10)
            if r.returncode == 0:
                return r.stdout
        except Exception:
            pass
        try:
            import pyautogui
            import io
            img = pyautogui.screenshot()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception:
            return None

    def lock_screen(self) -> bool:
        try:
            subprocess.run(["loginctl", "lock-session"], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def shutdown(self) -> bool:
        try:
            subprocess.run(["systemctl", "poweroff"], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def reboot(self) -> bool:
        try:
            subprocess.run(["systemctl", "reboot"], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def get_shell(self) -> str:
        return "/bin/bash"

    def install_package(self, name: str) -> bool:
        for mgr in [
            ["sudo", "apt", "install", "-y", name],
            ["sudo", "pacman", "-S", "--noconfirm", name],
            ["sudo", "dnf", "install", "-y", name],
        ]:
            try:
                r = subprocess.run(mgr, timeout=120, capture_output=True)
                if r.returncode == 0:
                    return True
            except Exception:
                continue
        return False

    def get_running_processes(self, top_n: int = 10) -> list[dict]:
        import psutil
        procs = []
        for p in psutil.process_iter(["name", "memory_info"]):
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
        protected = {"systemd", "init", "kernel", "sshd"}
        matches = []
        for p in psutil.process_iter(["name"]):
            try:
                process_name = (p.info["name"] or "").lower()
                process_stem = process_name.removesuffix(".exe")
                if process_stem == requested and process_stem not in protected and p.pid != psutil.Process().pid:
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
            r = subprocess.run(["wmctrl", "-l"], timeout=5, capture_output=True, text=True)
            lines = []
            for line in r.stdout.splitlines():
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    lines.append(parts[3])
            return lines
        except Exception:
            return []

    def focus_window(self, title: str) -> bool:
        try:
            subprocess.run(["wmctrl", "-a", title], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def minimize_all(self) -> bool:
        try:
            subprocess.run(["wmctrl", "-k", "on"], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def send_notification(self, title: str, message: str) -> bool:
        try:
            subprocess.run(["notify-send", title, message], timeout=5, capture_output=True)
            return True
        except Exception:
            return False

    def open_url(self, url: str) -> bool:
        try:
            subprocess.run(["xdg-open", url], timeout=5, capture_output=True)
            return True
        except Exception:
            return False
