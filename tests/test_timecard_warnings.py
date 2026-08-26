from app.validation.timecard import validate_timecard_transcription


def test_transcription_warns_about_odd_and_out_of_order_punches():
    transcription = {
        "pages": [
            {
                "page": 1,
                "days": [
                    {
                        "date_raw": "20",
                        "punches": [
                            {"time_hhmm": "09:00"},
                            {"time_hhmm": "18:00"},
                            {"time_hhmm": "12:00"},
                        ],
                    }
                ],
            }
        ]
    }

    warnings = validate_timecard_transcription(transcription)

    assert [warning.code for warning in warnings] == [
        "ODD_PUNCHES",
        "OUT_OF_ORDER_PUNCHES",
    ]
    assert all(warning.page == 1 for warning in warnings)
    assert all(warning.row == 0 for warning in warnings)

def test_transcription_warns_when_page_has_no_days():
    transcription = {
        "pages": [
            {
                "page": 1,
                "days": [],
            }
        ]
    }

    warnings = validate_timecard_transcription(transcription)

    assert len(warnings) == 1
    assert warnings[0].code == "EMPTY_PAGE"
    assert warnings[0].page == 1
    assert warnings[0].row is None