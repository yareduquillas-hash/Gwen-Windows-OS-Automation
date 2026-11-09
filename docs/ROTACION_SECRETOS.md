# Runbook de rotacion de secretos

La migracion local ya se ejecuto en esta PC:

- Las claves de entorno fueron verificadas en Windows Credential Manager.
- `.env` no contiene valores secretos.
- `Gwen Key.txt` fue eliminado.
- OAuth, memoria, configuracion y logs runtime salen del proyecto.
- La clave local antigua de API fue eliminada; la API permanece deshabilitada
  hasta crear una nueva.

## Claves externas

La revocacion debe hacerse en los paneles porque requiere la cuenta del usuario.

1. Telegram: revoca el token del bot mediante BotFather y genera uno nuevo.
2. NVIDIA NIM: revoca la API key anterior en `build.nvidia.com` y genera otra.
3. OpenRouter: revoca la key anterior y genera otra con limites de gasto.
4. Google: revoca el acceso OAuth en la cuenta Google y vuelve a autenticar
   Drive. El archivo nuevo debe quedar en `%APPDATA%\GwenWindowsPro\`.
5. Revisa y elimina permisos publicos de archivos que Gwen haya subido antes
   de esta correccion; las nuevas subidas quedan privadas.

No se deben pegar valores de claves en chats, issues, capturas ni commits.

## Nueva clave API local

Ejecuta desde la raiz del proyecto:

```powershell
python rotate_api_key.py --show
```

El script guarda una clave aleatoria de 32 bytes en Credential Manager. El
argumento `--show` la muestra una sola vez para introducirla en la pantalla de
conexion Android.
La aplicacion Android la almacena cifrada.

## Migraciones disponibles

```powershell
python migrate_secrets.py --redact-env --remove-legacy-key
python migrate_google_credentials.py
python migrate_runtime_data.py
```

`migrate_runtime_data.py --cleanup-source` solo debe ejecutarse despues de
detener todas las instancias de Gwen, porque SQLite y los logs pueden estar
bloqueados por Windows.
