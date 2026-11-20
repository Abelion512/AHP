"""The consolidation doc must describe every catalogued plugin."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_consolidation_doc_names_every_catalog_plugin():
    catalog = json.loads((ROOT / "hermes.json").read_text(encoding="utf-8"))
    doc = (ROOT / "docs" / "CONSOLIDATION.md").read_text(encoding="utf-8")
    ids = [entry["id"] for entry in catalog["plugins"]]
    assert ids
    for plugin_id in ids:
        assert plugin_id in doc
