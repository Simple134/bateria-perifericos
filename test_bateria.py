from importlib.machinery import SourceFileLoader

b = SourceFileLoader("bateria", "./bateria").load_module()
assert b.mv_to_percent(3000) == 0
assert b.mv_to_percent(4300) == 100
assert b.mv_to_percent(3750) == 50
assert 0 <= b.mv_to_percent(3938) <= 100
print("ok")

m = SourceFileLoader("bateria_menu", "./bateria_menu.py").load_module()
assert [m.level(p) for p in (100, 60, 59, 30, 29, 0)] == ["alta", "alta", "media", "media", "baja", "baja"]
assert not m.is_charging("descargando") and m.is_charging("cargando") and m.is_charging("con cable") and not m.is_charging("en batería")
assert m.hours_left([[0, 80], [3600, 76], [7200, 72]], 72, "x")[1] == "uso"
assert m.hours_left([[0, 90]], 90, "G305 Mouse") == (225.0, "especificación")
assert m.hours_left([[0, 90]], 90, "otro")[0] is None
assert m.title_for("G535 Wireless Gaming Headset") == "Audífonos G535"
assert m.title_for("G305 Lightspeed Wireless Gaming Mouse") == "Mouse G305"
assert m.title_for("2.4G Wireless Receiver (teclado)", {"2.4G Wireless Receiver (teclado)": "AULA F99"}) == "Teclado AULA F99"
assert m.title_for("2.4G Wireless Receiver (teclado)", {}) == "Teclado 2.4G Receiver"
print("ok menú")
