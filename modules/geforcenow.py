import threading
from modules.base import BaseModule
from utils.gfn_engine import GFNEngine


class GeForceNowModule(BaseModule):
    nombre = "geforcenow"
    prioridad = 45

    _engine: GFNEngine | None = None

    def _get_engine(self, cfg):
        if self._engine is None:
            self._engine = GFNEngine(cfg)
        return self._engine

    def can_handle(self, texto: str) -> bool:
        t = texto.lower().strip()
        triggers = (
            "prepárame el entorno de juego", "preparame el entorno de juego",
            "entorno de juego", "modo juego", "prepárame para jugar",
            "preparame para jugar", "quiero jugar",
            "juega a ", "jugar a ", "jugar ", "juega ",
            "lanza el juego ", "lanza ", "/lanza", "/oc_gfn",
            "abre geforce", "abrir geforce", "inicia geforce", "iniciar geforce",
            "cómo va la cola", "como va la cola", "estado de la cola",
            "qué posición en cola", "que posicion en cola",
            "posición de la cola", "posicion de la cola",
            "cuánto falta en la cola", "cuanto falta en la cola",
            "cancela la cola", "cancelar cola", "sal de la cola",
            "qué juegos tengo", "que juegos tengo",
            "abre geforce now", "abrir geforce now",
            "abre geforce y", "forzar monitoreo de cola", "cola de geforce",
            "cola de gfn", "estado de gfn",
        )
        return any(p in t for p in triggers)

    def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
        t = texto.lower().strip()
        engine = self._get_engine(cfg)

        # 1. Consulta explícita del estado de la cola
        if any(p in t for p in ("cómo va la cola", "como va la cola", "estado de la cola", "qué posición en cola", "que posicion en cola", "cuánto falta en la cola", "cuanto falta en la cola", "cola de geforce", "cola de gfn", "forzar monitoreo de cola")):
            engine.check_queue_status(chat_id, bot, cfg, platform)
            return True

        # 2. Cancelar monitoreo de la cola
        if any(p in t for p in ("cancela la cola", "cancelar cola", "sal de la cola")):
            game = self._extract_game(texto, t)
            engine.cancel_queue(game)
            if game:
                bot.send_message(chat_id, f"Monitoreo de cola cancelado para *{game}*, {cfg.user_title}.")
            else:
                bot.send_message(chat_id, f"Monitoreo de cola cancelado, {cfg.user_title}.")
            return True

        # 3. Listado de perfiles y juegos rápidos
        if any(p in t for p in ("qué perfiles tengo", "que perfiles tengo", "perfiles gfn", "perfiles de juego")):
            from utils.gfn_profiles import GFNProfileManager
            profs = GFNProfileManager().list_profiles()
            if profs:
                lines = [f"🎮 *Perfiles de inicio de sesión configurados:*\n"]
                for p in profs:
                    lines.append(f"  • *{p.game_name}* → `{p.profile_name}` ({p.account_email})")
                bot.send_message(chat_id, "\n".join(lines))
            else:
                bot.send_message(chat_id, "No hay perfiles de autologin configurados en `/gfn`.")
            return True

        if any(p in t for p in ("qué juegos tengo", "que juegos tengo")):
            games = getattr(cfg, 'gfn_quick_games', [])
            if games:
                bot.send_message(
                    chat_id,
                    f"🎮 *Juegos configurados en GeForce NOW, {cfg.user_title}:*\n" +
                    "\n".join(f"  • {g}" for g in games)
                )
            else:
                bot.send_message(chat_id, "No hay juegos configurados en GFN_QUICK_GAMES.")
            return True

        # 4. Abrir únicamente GeForce NOW
        if t in ("abre geforce", "abrir geforce", "inicia geforce", "abre geforce now", "abrir geforce now"):
            if engine.open():
                bot.send_message(chat_id, f"GeForce NOW abierto, {cfg.user_title}.")
            else:
                bot.send_message(chat_id, f"No pude abrir GeForce NOW. Verifique que esté instalado.")
            return True

        # 5. Lanzar un juego específico
        extracted = self._extract_game(texto, t)
        if extracted:
            game, profile = self._parse_game_and_profile(extracted)
            threading.Thread(
                target=engine.launch_game,
                args=(game, chat_id, bot, cfg, platform, profile),
                daemon=True,
            ).start()
            return True
        elif any(p in t for p in ("lanza", "juega", "quiero jugar")):
            games = getattr(cfg, 'gfn_quick_games', [])
            if games:
                default_game = games[0]
                bot.send_message(chat_id, f"No especificó juego. Usando: *{default_game}*...")
                threading.Thread(
                    target=engine.launch_game,
                    args=(default_game, chat_id, bot, cfg, platform, None),
                    daemon=True,
                ).start()
                return True
            bot.send_message(chat_id, f"¿Qué juego desea lanzar, {cfg.user_title}?")
            return True

        return False

    def _extract_game(self, texto: str, t_lower: str) -> str | None:
        prefixes = (
            "prepárame el entorno de juego para ", "preparame el entorno de juego para ",
            "prepárame el entorno de juego", "preparame el entorno de juego",
            "entorno de juego para ", "modo juego para ",
            "prepárame para jugar a ", "preparame para jugar a ",
            "prepárame para jugar ", "preparame para jugar ",
            "quiero jugar a ", "quiero jugar ",
            "juega a ", "juega ", "lanza el juego ", "lanza ", "/lanza ", "/oc_gfn ",
            "jugar a ", "jugar ", "abre geforce y pon ", "abre geforce y ",
            "abre y pon "
        )
        for pref in prefixes:
            if pref in t_lower:
                rest = texto.split(pref, 1)[-1].strip().strip('"').strip("'").lstrip("-:").strip()
                if rest and len(rest) > 1 and not rest.lower().startswith("geforce"):
                    return rest
        return None

    def _parse_game_and_profile(self, text: str) -> tuple[str, str | None]:
        """Separa el nombre del juego de un perfil opcional (ej: 'genshin perfil principal')."""
        t = text.strip()
        for sep in (" perfil ", " cuenta ", " con perfil ", " con cuenta "):
            if sep in t.lower():
                parts = t.lower().split(sep, 1)
                idx = t.lower().find(sep)
                game = t[:idx].strip()
                prof = t[idx + len(sep):].strip()
                return game, prof or None
        # Si tiene formato 'juego:perfil'
        if ":" in t:
            parts = t.split(":", 1)
            return parts[0].strip(), parts[1].strip() or None
        return t, None


MODULE_CLASS = GeForceNowModule
