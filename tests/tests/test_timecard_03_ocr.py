import shutil

import pytest

from app.transcription import parse_timecard


pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="Teste de OCR exige Tesseract; execute a suíte completa no Docker.",
)


def test_timecard_03_ocr_preserves_visual_order():
    page = parse_timecard("time-card-03.pdf")["pages"][0]

    days = {
        day["date_raw"]: [
            punch["time_hhmm"]
            for punch in day["punches"]
        ]
        for day in page["days"]
    }

    assert days["16/12/2019"] == [
        "07:00",
        "12:00",
        "13:00",
        "17:00",
    ]