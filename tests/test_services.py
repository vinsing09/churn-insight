"""Unit tests for services that don't require external API calls."""
from app.services.pii_strip import strip_pii


def test_strip_email():
    result = strip_pii("Contact me at john@example.com for details")
    assert "[EMAIL]" in result
    assert "john@example.com" not in result


def test_strip_phone():
    result = strip_pii("Call me at 415-555-1234 anytime")
    assert "[PHONE]" in result
    assert "415-555-1234" not in result


def test_strip_person_name():
    result = strip_pii("Hi, my name is John Smith and I cancelled")
    assert "John Smith" not in result


def test_strip_url():
    result = strip_pii("I found a better tool at https://competitor.com")
    assert "[URL]" in result
    assert "https://competitor.com" not in result


def test_no_pii_unchanged():
    text = "The product was too expensive for our budget."
    result = strip_pii(text)
    assert result == text
