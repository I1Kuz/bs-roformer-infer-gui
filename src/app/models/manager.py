import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import cast, final

from app.core.logging import get_logger
from app.core.paths import get_python_exe, get_src_dir, get_worker_script_path

logger = get_logger(__name__)


@dataclass(slots=True)
class ModelMetadata:
    id: str
    name: str
    category: str
    stems: list[str]
    checkpoint: str
    installed: bool = False


@final
class ModelManager:
    def __init__(self) -> None:
        self.python_exe: Path = get_python_exe()
        self.src_dir: Path = get_src_dir()
        self.models: dict[str, ModelMetadata] = {}

    def fetch_registry(self) -> bool:
        if not self.python_exe.exists():
            logger.warning("Python runtime not found. Cannot fetch registry.")
            return False

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.src_dir)

            result = subprocess.run(
                [str(self.python_exe), str(get_worker_script_path()), "--registry"],
                capture_output=True,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=str(self.src_dir),
                env=env,
            )

            if result.returncode != 0:
                logger.error(
                    "Failed to fetch registry with return code %d: %s",
                    result.returncode,
                    result.stderr.strip(),
                )
                return False

            raw: object = json.loads(result.stdout.strip())
            if not isinstance(raw, dict):
                logger.error("Unexpected registry response format")
                return False

            data = cast(dict[str, object], raw)
            if data.get("status") != "success":
                return False

            items_raw = data.get("data", [])
            if not isinstance(items_raw, list):
                return False
            items = cast(list[object], items_raw)

            self.models.clear()
            for raw_item in items:
                if not isinstance(raw_item, dict):
                    continue
                item_data = cast(dict[str, object], raw_item)

                name_str = str(item_data.get("name", ""))
                if name_str.startswith("Roformer Model: "):
                    name_str = name_str.removeprefix("Roformer Model: ")

                stems_raw = item_data.get("stems", [])
                stems = [str(s) for s in cast(list[object], stems_raw)] if isinstance(stems_raw, list) else []

                meta = ModelMetadata(
                    id=str(item_data.get("id", "")),
                    name=name_str,
                    category=str(item_data.get("category", "")),
                    stems=stems,
                    checkpoint=str(item_data.get("checkpoint", "")),
                    installed=bool(item_data.get("installed", False)),
                )
                self.models[meta.id] = meta

            logger.info("Loaded %d models from registry", len(self.models))
            return True

        except Exception as e:
            logger.error("Error fetching registry: %s", e)
            return False

    def get_all_models(self) -> list[ModelMetadata]:
        return list(self.models.values())

    def get_model(self, model_id: str) -> ModelMetadata | None:
        return self.models.get(model_id)
