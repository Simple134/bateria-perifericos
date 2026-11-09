#!/bin/bash
# Quita el inicio automático y cierra el panel. No borra la carpeta ni el historial.
LABEL="com.bateria.perifericos"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
echo "Desinstalado. El historial sigue en ~/.bateria-perifericos (bórralo si no lo quieres)."
