"""The static page (docs/): strict content policy, own files only, complete translations."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")


def test_the_content_policy_allows_only_own_files_and_the_assistant():
    [csp] = re.findall(r'http-equiv="Content-Security-Policy" content="([^"]+)"', HTML)
    rules = dict(part.strip().split(" ", 1) for part in csp.split(";"))
    assert rules["default-src"] == "'none'"
    assert rules["script-src"] == rules["style-src"] == rules["img-src"] == "'self'"
    assert "https://cv-api.onsorex.com" in rules["connect-src"]
    assert "unsafe" not in csp


def test_no_inline_scripts_styles_or_third_party_files():
    assert not re.search(r"<script(?![^>]*\bsrc=)", HTML)  # every script is a file
    assert "<style" not in HTML and ' style="' not in HTML
    assert "fonts.googleapis" not in HTML
    for ref in re.findall(r'(?:src|href)="([^"#:]+)"', HTML):  # local references
        assert (ROOT / "docs" / ref).is_file(), ref


def test_every_text_has_a_german_and_a_persian_version():
    keys = set(re.findall(r'data-i18n="([^"]+)"', HTML))
    for key in keys - {"hero.name"}:  # the name stays the same in German
        assert len(re.findall(rf'"{re.escape(key)}":', JS)) == 2, key


def test_suggestion_buttons_ask_for_prepared_answers_that_exist():
    ids = {item["id"] for item in json.loads((ROOT / "knowledge" / "answers.json").read_text(encoding="utf-8"))}
    chips = re.findall(r'\["([a-z-]+)", "[^"]+"\]', JS)
    assert len(chips) == 21 and set(chips) <= ids


def test_the_api_address_can_only_be_overridden_to_this_computer():
    assert '"https://cv-api.onsorex.com"' in JS
    assert r"/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/" in JS
