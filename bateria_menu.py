#!/usr/bin/env python3
"""Panel en la barra de menú con la batería de los periféricos y su autonomía estimada."""
import json
import re
import sys
import threading
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

import objc
from AppKit import (
    NSApplication, NSApplicationActivationPolicyAccessory, NSBezierPath, NSColor, NSFont, NSImage,
    NSImageLeft, NSMakeRect, NSMakeSize, NSMinYEdge, NSPopover, NSPopoverBehaviorTransient,
    NSStatusBar, NSVariableStatusItemLength, NSViewController,
)
from Foundation import NSObject
from PyObjCTools import AppHelper
from WebKit import WKWebView, WKWebViewConfiguration

HERE = Path(__file__).resolve().parent
bateria = SourceFileLoader("bateria", str(HERE / "bateria")).load_module()

HISTORY = Path.home() / ".bateria-perifericos" / "historial.json"
POLL_SECONDS = 60
LOCK = threading.Lock()
HIGH, MID = 60, 30  # alta desde 60 %, media desde 30 %, baja por debajo

# Autonomía publicada por el fabricante, en horas con el 100 %. Se usa hasta tener datos propios.
SPEC_HOURS = {"G305": 250, "G535": 33}
NAMES = Path.home() / ".bateria-perifericos" / "nombres.json"
SOURCE_TEXT = {"uso": "Según tu uso reciente", "especificación": "Según la especificación del fabricante"}


def level(pct):
    return "alta" if pct >= HIGH else "media" if pct >= MID else "baja"


def is_charging(note):
    return note.startswith(("cargando", "llena", "casi llena")) or "cable" in note


def load_history():
    try:
        return json.loads(HISTORY.read_text())
    except (OSError, ValueError):
        return {}


def record(history, name, pct, now):
    samples = history.setdefault(name, [])
    if not samples or samples[-1][1] != pct or now - samples[-1][0] > 600:
        samples.append([now, pct])
    history[name] = [s for s in samples if now - s[0] < 7 * 86400]


def hours_left(samples, pct, name):
    """Horas restantes y su origen: 'uso' si sale del ritmo medido, 'especificación' si no hay datos."""
    run = samples[-1:]
    for s in reversed(samples[:-1]):
        if s[1] + 3 < run[0][1]:  # la carga subió: empieza otro ciclo
            break
        run.insert(0, s)
    span_h = (run[-1][0] - run[0][0]) / 3600
    drop = run[0][1] - run[-1][1]
    if span_h >= 1 and drop >= 3:
        return pct / (drop / span_h), "uso"
    spec = next((h for key, h in SPEC_HOURS.items() if key in name), None)
    return (pct / 100 * spec, "especificación") if spec else (None, "")


def fmt_hours(h):
    if h < 1:
        return f"{round(h * 60)} min"
    return f"{h:.0f} h" if h < 48 else f"{h / 24:.0f} días"


def load_aliases():
    """Nombres propios opcionales: {"2.4G Wireless Receiver (teclado)": "AULA F99"}."""
    try:
        return json.loads(NAMES.read_text())
    except (OSError, ValueError):
        return {}


def title_for(name, aliases=None):
    lower = name.lower()
    kind = "Teclado" if "teclado" in lower else "Audífonos" if "headset" in lower else "Mouse" if "mouse" in lower else ""
    short = (load_aliases() if aliases is None else aliases).get(name) or re.sub(r"\b(Wireless|Gaming|Lightspeed|Headset|Mouse)\b\s*|\s*\(teclado\)", "", name).strip()
    return f"{kind} {short}".strip()


def card(name, pct, note, **extra):
    return {"title": title_for(name), "pct": pct, "level": level(pct) if pct is not None else None, "note": note,
            "charging": False, "stale": False, "hours": "", "source": "", "seen": None, **extra}


def collect_state():
    try:
        rows = bateria.read_all()
    except Exception as e:  # una lectura fallida no debe tumbar el panel
        rows = [("Error al leer", None, str(e))]
    history, now = load_history(), time.time()
    live = {r[0] for r in rows if r[1] is not None}
    out = []
    for name, pct, note in rows:
        if pct is None and name not in live and history.get(name):
            continue  # se muestra más abajo con su última lectura
        if pct is None:
            out.append(card(name, None, note))
            continue
        record(history, name, pct, now)
        charging = is_charging(note)
        hours, source = (None, "") if charging else hours_left(history[name], pct, name)
        out.append(card(name, pct, note, charging=charging, hours=f"~{fmt_hours(hours)} restantes" if hours else "",
                        source=SOURCE_TEXT.get(source, "")))
    for name, samples in history.items():
        if name not in live and now - samples[-1][0] < 86400:
            out.append(card(name, samples[-1][1], "", stale=True, seen=samples[-1][0]))
    HISTORY.parent.mkdir(exist_ok=True)
    HISTORY.write_text(json.dumps(history))
    return {"rows": out, "updated": now, "loading": False}


def battery_icon(pct):
    """Batería dibujada: contorno del sistema y relleno con el color de estado."""
    color = {None: NSColor.tertiaryLabelColor(), "alta": NSColor.systemGreenColor(),
             "media": NSColor.systemOrangeColor(), "baja": NSColor.systemRedColor()}[level(pct) if pct is not None else None]

    def draw(_rect):
        NSColor.secondaryLabelColor().setStroke()
        NSColor.secondaryLabelColor().setFill()
        body = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(1.5, 1.5, 19, 9), 2.5, 2.5)
        body.setLineWidth_(1)
        body.stroke()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(21, 4, 2, 4), 1, 1).fill()
        if pct is not None:
            color.setFill()
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(3, 3, max(1.5, 16 * pct / 100), 6), 1.2, 1.2).fill()
        return True

    return NSImage.imageWithSize_flipped_drawingHandler_(NSMakeSize(24, 12), False, draw)


class Bridge(NSObject, protocols=[objc.protocolNamed("WKScriptMessageHandler")]):
    def initWithApp_(self, app):
        self = objc.super(Bridge, self).init()
        self.app = app
        return self

    def userContentController_didReceiveScriptMessage_(self, _controller, message):
        body = str(message.body())
        if body == "refresh":
            threading.Thread(target=self.app.poll, daemon=True).start()
        elif body == "quit":
            NSApplication.sharedApplication().terminate_(None)
        elif body.startswith("size:"):
            self.app.pop.setContentSize_(NSMakeSize(320, int(body[5:])))


class Delegate(NSObject):
    def applicationDidFinishLaunching_(self, _note):
        self.item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        button = self.item.button()
        button.setTarget_(self)
        button.setAction_("toggle:")
        button.setImagePosition_(NSImageLeft)
        button.setFont_(NSFont.monospacedDigitSystemFontOfSize_weight_(12, 0.0))
        self.paint(None)

        config = WKWebViewConfiguration.alloc().init()
        self.bridge = Bridge.alloc().initWithApp_(self)
        config.userContentController().addScriptMessageHandler_name_(self.bridge, "bridge")
        self.web = WKWebView.alloc().initWithFrame_configuration_(NSMakeRect(0, 0, 320, 160), config)
        self.web.setValue_forKey_(False, "drawsBackground")
        self.web.loadHTMLString_baseURL_((HERE / "panel.html").read_text(), None)
        controller = NSViewController.alloc().init()
        controller.setView_(self.web)
        self.pop = NSPopover.alloc().init()
        self.pop.setBehavior_(NSPopoverBehaviorTransient)
        self.pop.setContentViewController_(controller)
        self.pop.setContentSize_(NSMakeSize(320, 160))

        threading.Thread(target=self.loop, daemon=True).start()
        if "--abrir" in sys.argv:
            AppHelper.callLater(5, self.toggle_, None)

    def toggle_(self, _sender):
        if self.pop.isShown():
            self.pop.performClose_(None)
            return
        button = self.item.button()
        self.pop.showRelativeToRect_ofView_preferredEdge_(button.bounds(), button, NSMinYEdge)
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)

    @objc.python_method
    def loop(self):
        while True:
            self.poll()
            time.sleep(POLL_SECONDS)

    @objc.python_method
    def poll(self):
        with LOCK:
            state = collect_state()
        AppHelper.callAfter(self.apply, state)

    @objc.python_method
    def apply(self, state):
        known = [r["pct"] for r in state["rows"] if r["pct"] is not None]
        self.paint(min(known) if known else None)
        self.web.evaluateJavaScript_completionHandler_(f"render({json.dumps(state)})", None)

    @objc.python_method
    def paint(self, pct):
        button = self.item.button()
        button.setImage_(battery_icon(pct))
        button.setTitle_(f" {pct}%" if pct is not None else " --")


if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = Delegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
