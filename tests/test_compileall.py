import compileall
from pathlib import Path

def test_compileall_src():
    src = Path(__file__).resolve().parents[1] / "src"
    ok = compileall.compile_dir(str(src), quiet=1)
    assert ok, "Python source should compile (catches indentation/syntax errors)"
