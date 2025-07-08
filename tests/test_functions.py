from pathlib import Path
from difflib import SequenceMatcher

class StubPD:
    def isna(self, x):
        return x is None or x != x
    def notna(self, x):
        return not self.isna(x)


def load_functions():
    path = Path(__file__).resolve().parents[1] / "main.py"
    lines = path.read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("def limpiar_codigo_color_mejorado"))
    end = next(i for i, l in enumerate(lines) if l.startswith("def determinar_confianza_mejorada"))
    code = "\n".join(lines[start:end])
    namespace = {"pd": StubPD(), "SequenceMatcher": SequenceMatcher}
    exec(code, namespace)
    return namespace


def test_normalizar_talla_numeric_and_alpha():
    funcs = load_functions()
    norm = funcs["normalizar_talla"]
    assert norm("22") == "XXS"
    assert norm("24") == "XS"
    assert norm("26") == "S"
    assert norm("28") == "M"
    assert norm("32") == "XL"
    assert norm("36") == "XXXL"
    assert norm("m") == "M"
    assert norm("XL") == "XL"
    assert norm("unknown") == "UNKNOWN"


def test_score_with_matching_talla_after_normalization():
    funcs = load_functions()
    norm = funcs["normalizar_talla"]
    calc = funcs["calcular_score_similitud_mejorado_final"]
    demanda = {"categoria": "Camisa", "color": "Rojo", "talla": "28"}
    producto = {"Categoria": "Camisa", "color": "ROJO", "talla": "M"}
    demanda["talla_normalizada"] = norm(demanda["talla"])
    producto["talla_normalizada"] = norm(producto["talla"])
    config = {"incluir_similares": False, "ignorar_tallas": False, "limpiar_codigos": True}
    score = calc(demanda, producto, config)
    assert score == 100
