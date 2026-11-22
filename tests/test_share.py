import xml.dom.minidom
from core.demo import load_demo
from ui.proof_card import build_share_svg, build_proof_html


def test_share_svg_wellformed_en_bn():
    c = load_demo("vaccines_en")
    for lang in ("en", "bn"):
        svg = build_share_svg("A <b> topic & more", lang, 40, 80, c.analysis.concepts, {"C2": 2, "C5": 1, "C4": 1})
        xml.dom.minidom.parseString(svg)
        assert "&lt;b&gt;" in svg
