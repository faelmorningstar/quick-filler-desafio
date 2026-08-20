from app.timecard.parser import parse_page_text


def test_parse_page_text_builds_days_and_punches():
    text = """
    21/05/2019
    08:25
    18:25
    22/05/2019
    08:30
    12:00
    13:00
    18:20
    """

    result = parse_page_text(text)

    assert len(result) == 2

    assert result[0].date_raw == "21/05/2019"
    assert result[0].punches[0].kind == "IN"
    assert result[0].punches[0].time_hhmm == "08:25"
    assert result[0].punches[1].kind == "OUT"

    assert result[1].date_raw == "22/05/2019"
    assert len(result[1].punches) == 4
    assert result[1].punches[2].kind == "IN"
    assert result[1].punches[3].kind == "OUT"