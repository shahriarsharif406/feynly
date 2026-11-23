import os
os.environ.pop("GEMINI_API_KEY", None)
from streamlit.testing.v1 import AppTest


def _app():
    at = AppTest.from_file(str(__import__("pathlib").Path(__file__).resolve().parent.parent / "app.py"), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def _btn(at, frag):
    return next(b for b in at.button if frag in b.label)


def test_full_demo_loop_en():
    at = _app()
    _btn(at, "sample").click().run()
    assert not at.exception, at.exception
    assert at.session_state["stage"] == "gaps"
    assert at.session_state["before_score"] == 50
    _btn(at, "ready").click().run()
    assert not at.exception, at.exception
    assert at.session_state["stage"] == "proof"
    _btn(at, "sample answers").click().run()
    _btn(at, "Submit").click().run()
    assert not at.exception, at.exception
    assert at.session_state["after_score"] == 90


def test_full_demo_loop_bn_code():
    at = _app()
    at.session_state["lang"] = "bn"
    at.session_state["mode"] = "code"
    at.run()
    _btn(at, "নমুনা").click().run()
    assert not at.exception, at.exception
    assert at.session_state["before_score"] == 38
    _btn(at, "তৈরি").click().run()
    _btn(at, "নমুনা উত্তর").click().run()
    _btn(at, "উত্তর জমা").click().run()
    assert not at.exception, at.exception
    assert at.session_state["after_score"] == 88


def test_sample_picker_and_class_code():
    at = _app()
    at.selectbox[0].select("vaccines_en").run()
    at.text_input(key="in_class").set_value("bio-9a").run()
    _btn(at, "sample").click().run()
    assert not at.exception, at.exception
    assert at.session_state["before_score"] == 40


def test_run_demo_instead_after_ai_error():
    at = _app()
    at.session_state["error_key"] = "err_ai_busy"
    at.run()
    _btn(at, "demo").click().run()
    assert not at.exception, at.exception
    assert at.session_state["stage"] == "gaps"
