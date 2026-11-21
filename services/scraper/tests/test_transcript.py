import json

from app.collectors.youtube import _caption_track, parse_json3, parse_vtt


def test_parse_json3_joins_segments():
    payload = json.dumps({"events": [{"segs": [{"utf8": "Zarabiaj "}, {"utf8": "z nami"}]}, {"segs": [{"utf8": "\n"}]}, {"segs": [{"utf8": "bez ryzyka"}]}]})
    assert parse_json3(payload) == "Zarabiaj z nami bez ryzyka"


def test_parse_vtt_drops_timestamps_and_duplicate_lines():
    payload = "WEBVTT\nKind: captions\n\n00:00:01.000 --> 00:00:03.000\nPierwsza <c>linia</c>\n\n00:00:03.000 --> 00:00:05.000\nPierwsza linia\nDruga linia\n"
    assert parse_vtt(payload) == "Pierwsza linia Druga linia"


def test_caption_track_prefers_manual_polish_json3():
    info = {
        "subtitles": {"pl": [{"ext": "vtt", "url": "u1"}, {"ext": "json3", "url": "u2"}]},
        "automatic_captions": {"pl": [{"ext": "json3", "url": "u3"}]},
    }
    assert _caption_track(info)["url"] == "u2"
    assert _caption_track({}) is None
