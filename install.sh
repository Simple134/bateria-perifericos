#!/bin/bash
# Instala las dependencias en .venv y deja el panel arrancando al iniciar sesión.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.bateria.perifericos"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

[ "$(uname)" = "Darwin" ] || { echo "Solo funciona en macOS." >&2; exit 1; }
command -v python3 >/dev/null || { echo "Falta python3. Instala las Xcode Command Line Tools: xcode-select --install" >&2; exit 1; }

python3 -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q -U pip
"$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt"

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$LABEL</string>
    <key>ProgramArguments</key>
    <array><string>$DIR/.venv/bin/python</string><string>$DIR/bateria_menu.py</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
    <key>StandardErrorPath</key><string>$HOME/.bateria-perifericos.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Listo. El icono de batería aparece en la barra de menú."
echo "Si el teclado 2.4G no responde: Ajustes del Sistema > Privacidad y seguridad > Monitoreo de entrada, y añade $DIR/.venv/bin/python"
