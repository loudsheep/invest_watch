import json

import pytest
from app.collectors import dataset
from app.collectors.dataset import DatasetCollector


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "DATASET_DIR", tmp_path)
    return tmp_path


def collect(collector):
    return [collector.fetch(c) for c in collector.discover()]


def test_reads_jsonl_json_and_csv(data_dir):
    (data_dir / "a.jsonl").write_text(json.dumps({"url": "https://a.pl", "tekst": "Zysk bez ryzyka"}) + "\n")
    (data_dir / "b.json").write_text(json.dumps([{"link": "https://b.pl", "content": "Doradztwo", "label": {"m3": True}}]))
    (data_dir / "c.csv").write_text("url,text,label\nhttps://c.pl,Kod promo,true\n", encoding="utf-8")

    docs = collect(DatasetCollector({}))

    assert [d.url for d in docs] == ["https://a.pl", "https://b.pl", "https://c.pl"]
    assert docs[1].extra["label"] == {"m3": True}
    assert docs[2].extra["label"] is True


def test_record_without_content_is_skipped(data_dir):
    (data_dir / "x.json").write_text(json.dumps({"url": "https://x.pl"}))
    assert collect(DatasetCollector({})) == [None]


def test_missing_directory_yields_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(dataset, "DATASET_DIR", tmp_path / "absent")
    assert collect(DatasetCollector({})) == []
