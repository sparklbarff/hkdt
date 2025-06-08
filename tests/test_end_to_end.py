from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hkdt_v3

def test_scan_file_sample():
    res = hkdt_v3.scan_file(Path('tests/data/sample.txt'))
    assert ["silent pond", "a frog jumps into", "the pond splash"] in res
