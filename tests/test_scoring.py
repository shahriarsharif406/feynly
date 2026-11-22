from core.scoring import round_half_up, band


def test_round_half_up():
    assert round_half_up(62.5) == 63 and round_half_up(12.4) == 12


def test_bands():
    assert [band(x) for x in (39, 40, 69, 70, 89, 90)] == ["cracked", "shaping", "shaping", "mended", "mended", "golden"]
