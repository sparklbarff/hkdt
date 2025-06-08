from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hkdt_v3

def test_sliding_windows():
    words = [
        "Cat", "Dog", "Bird", "Fish", "Mouse",
        "One", "Two", "Three", "Four", "Five", "Six", "Book",
        "Moon", "Star", "Sun", "Sky", "Cloud",
    ]
    result = list(hkdt_v3.sliding_windows(words, (5, 7, 5)))
    assert result == [[
        "Cat Dog Bird Fish Mouse",
        "One Two Three Four Five Six Book",
        "Moon Star Sun Sky Cloud",
    ]]


def test_simple_clean():
    raw = "Hello, World! Apples & Oranges."
    cleaned = hkdt_v3.simple_clean(raw)
    assert cleaned == "hello world apples oranges"
