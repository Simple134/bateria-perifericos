# Batería de periféricos

Icono en la barra de menú de macOS que muestra la carga de tus periféricos inalámbricos y cuánto te durará.

Al hacer clic se abre un panel con una tarjeta por dispositivo: porcentaje, barra de color, estado ("Carga alta", "Carga media", "Carga baja", "Cargando") y autonomía estimada. El icono de la barra toma el color del dispositivo con menos carga.

## Instalación

Requiere macOS y `python3` (viene con las Xcode Command Line Tools: `xcode-select --install`).

1. Descarga el `.zip` de la [última versión](../../releases/latest) y descomprímelo.
2. Desde esa carpeta ejecuta:

```bash
./install.sh
```

Crea un entorno virtual con las dependencias, registra un agente de inicio y abre el panel. Para quitarlo: `./uninstall.sh`.

También puedes leer la batería desde la terminal, sin el icono:

```bash
.venv/bin/python bateria
```

## Qué dispositivos lee

| Dispositivo | Cómo se lee | Probado |
|---|---|---|
| Bluetooth y Apple (Magic Mouse, teclados, AirPods...) | El porcentaje que ya reporta macOS (`ioreg`) | No, sin hardware para probarlo |
| Logitech con receptor Lightspeed/Unifying | HID++ 2.0, batería real | Mouse G305 |
| Logitech con conexión USB directa | HID++ 2.0, por voltaje (estimado) | Audífonos G535 |
| Teclados con receptor Compx `3554:fa09` (AULA, entre otros) | Comando `0x4A` del reporte `0x13` | AULA F99 |

Los demás teclados y ratones se muestran en la lista como "sin batería HID estándar": macOS los ve, pero no hay forma documentada de pedirles la carga.

Notas:

- **Audífonos G535:** no reportan un porcentaje. Se calcula con el voltaje y una curva típica de litio, así que es aproximado.
- **Dispositivos que duermen:** el mouse y el teclado dejan de responder cuando no se usan. El panel conserva la última lectura y la marca como "Sin lectura reciente".
- **Teclado con receptor Compx:** macOS pide el permiso de Monitoreo de entrada. Añade `.venv/bin/python` en Ajustes del Sistema > Privacidad y seguridad > Monitoreo de entrada.
- El protocolo del receptor Compx lo documentaron otros proyectos ([HaloBattery](https://github.com/ahmedkhursheed23/HaloBattery), [mousedock](https://github.com/late-autumn-gif/mousedock), [aula-f75-linux](https://github.com/trenbolone1122/aula-f75-linux)). Aquí solo se envía la consulta de batería, nunca configuración, luces ni firmware.

## Tiempo estimado

Al principio usa la autonomía publicada por el fabricante (`SPEC_HOURS` en `bateria_menu.py`: G305 250 h, G535 33 h). Cuando tiene al menos una hora de historial y una bajada de 3 puntos, calcula el ritmo real de tu uso. El historial se guarda en `~/.bateria-perifericos/historial.json`.

## Personalizar

- **Colores del icono y de las barras:** alta desde 60 %, media desde 30 %, baja por debajo (`HIGH` y `MID` en `bateria_menu.py`).
- **Nombre de un receptor genérico:** crea `~/.bateria-perifericos/nombres.json`, por ejemplo `{"2.4G Wireless Receiver (teclado)": "AULA F99"}`.
- **Actualización:** cada 60 segundos, o con el botón de actualizar del panel.

## Desarrollo

```bash
.venv/bin/python test_bateria.py
.venv/bin/python bateria_menu.py --abrir   # abre el panel a los 5 segundos
```

El diseño del panel está descrito en [DESIGN.md](DESIGN.md).

## Licencia

MIT. Ver [LICENSE](LICENSE).
