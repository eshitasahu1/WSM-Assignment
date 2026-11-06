"""Entry point.  Usage: python main.py [documents_folder]"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ir.engine import SearchEngine  # noqa: E402
from gui import SearchApp  # noqa: E402


def main() -> None:
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data")
    engine = SearchEngine(folder)
    try:
        engine.build_index()          # build once at start-up; the GUI can rebuild later
    except (FileNotFoundError, ValueError) as err:
        print(f"Starting without an index: {err}")
    SearchApp(engine).mainloop()


if __name__ == "__main__":
    main()
