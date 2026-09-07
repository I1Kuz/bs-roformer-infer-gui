import os
import sys
from pathlib import Path

# Ensure src/ is in the PYTHONPATH so imports like `from app.core...` work
current_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(current_dir))

from app.core.logging import setup_logging
from app.core.paths import ensure_directories, get_models_dir
from app.gui.main_window import MainWindow


def main() -> None:
    ensure_directories()
    # Force the library to use our appdata models directory
    os.environ["BS_ROFORMER_MODELS_PATH"] = str(get_models_dir())

    _ = setup_logging()

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
