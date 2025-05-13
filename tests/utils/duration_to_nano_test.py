import pytest
from containup.utils.duration_to_nano import duration_to_nano


def test_duration_to_nano_with_ns() -> None:
    assert duration_to_nano("1ns") == 1
    assert duration_to_nano("10ns") == 10
    assert duration_to_nano("999ns") == 999


def test_duration_to_nano_with_us() -> None:
    assert duration_to_nano("1us") == 1_000
    assert duration_to_nano("10us") == 10_000
    assert duration_to_nano("999us") == 999_000
    assert duration_to_nano("1µs") == 1_000
    assert duration_to_nano("10µs") == 10_000
    assert duration_to_nano("999µs") == 999_000


def test_duration_to_nano_with_ms() -> None:
    assert duration_to_nano("1ms") == 1_000_000
    assert duration_to_nano("10ms") == 10_000_000
    assert duration_to_nano("999ms") == 999_000_000
    assert duration_to_nano("1ms") == 1_000_000
    assert duration_to_nano("10ms") == 10_000_000
    assert duration_to_nano("999ms") == 999_000_000


def test_duration_to_nano_with_s() -> None:
    assert duration_to_nano("1s") == 1_000_000_000
    assert duration_to_nano("10s") == 10_000_000_000
    assert duration_to_nano("999s") == 999_000_000_000


def test_duration_to_nano_with_m() -> None:
    assert duration_to_nano("1m") == 1_000_000_000 * 60
    assert duration_to_nano("10m") == 10_000_000_000 * 60
    assert duration_to_nano("999m") == 999_000_000_000 * 60


def test_duration_to_nano_with_h() -> None:
    assert duration_to_nano("1h") == 1_000_000_000 * 60 * 60
    assert duration_to_nano("10h") == 10_000_000_000 * 60 * 60
    assert duration_to_nano("99h") == 99_000_000_000 * 60 * 60


def test_unknown_unit():
    with pytest.raises(ValueError, match="Unknown unit: 'bidule'"):
        assert duration_to_nano("1bidule")


def test_no_number_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid duration format: 'truc'"):
        assert duration_to_nano("truc")


def test_decimals_then_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid duration format: '123.45s'"):
        assert duration_to_nano("123.45s")


def test_empty_then_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid duration format: ''"):
        assert duration_to_nano("")


def test_no_unit_then_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid duration format: '1234'"):
        assert duration_to_nano("1234")


def test_unit_invalid_case_then_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid duration format: '1234S'"):
        assert duration_to_nano("1234S")


def test_duration_too_large() -> None:
    with pytest.raises(ValueError, match="Duration too large"):
        assert duration_to_nano("1000h")
