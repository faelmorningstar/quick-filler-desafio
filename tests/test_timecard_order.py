from app.transcription import _order_time_words


def test_moves_final_exit_after_interval_times():
    time_words = [
        (77.0, "09:00"),
        (104.0, "18:00"),
        (144.0, "12:00"),
        (170.0, "13:00"),
    ]

    assert _order_time_words(time_words, first_interval_x=140.0) == [
        "09:00",
        "12:00",
        "13:00",
        "18:00",
    ]

def test_keeps_visual_order_without_interval_header():
    time_words = [
        (95.0, "07:00"),
        (124.4, "12:00"),
        (153.8, "13:00"),
        (182.9, "17:00"),
    ]

    assert _order_time_words(time_words, first_interval_x=None) == [
        "07:00",
        "12:00",
        "13:00",
        "17:00",
    ]