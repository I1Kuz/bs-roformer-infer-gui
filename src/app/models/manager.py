import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger
from app.core.paths import get_runtime_dir, get_worker_script_path

logger = get_logger(__name__)


@dataclass(slots=True)
class ModelMetadata:
    id: str
    name: str
    category: str
    stems: list[str]
    checkpoint: str
    installed: bool = False


class ModelManager:
    def __init__(self) -> None:
        self.python_exe: Path = get_runtime_dir() / "python.exe"
        self.worker_script: Path = get_worker_script_path()
        self.models: dict[str, ModelMetadata] = {}

    def fetch_registry(self) -> bool:
        if not self.python_exe.exists():
            logger.warning("Python runtime not found. Cannot fetch registry.")
            return False

        try:
            result = subprocess.run(
                [str(self.python_exe), str(self.worker_script), "--registry"],
                capture_output=True,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout.strip())
                if data.get("status") == "success":
                    self.models.clear()
                    for item in data.get("data", []):
                        name_str = item.get("name", "")
                        if name_str.startswith("Roformer Model: "):
                            name_str = name_str.replace("Roformer Model: ", "")

                        meta = ModelMetadata(
                            id=item.get("id", ""),
                            name=name_str,
                            category=item.get("category", ""),
                            stems=list(item.get("stems", [])),
                            checkpoint=item.get("checkpoint", ""),
                            installed=bool(item.get("installed", False)),
                        )
                        self.models[meta.id] = meta
                    logger.info("Loaded %d models from registry", len(self.models))
                    return True
            else:
                logger.error("Failed to fetch registry with return code %d: %s", result.returncode, result.stderr.strip())
                return False
        except Exception as e:
            logger.error("Error fetching registry: %s", e)
            return False
        return False

    def get_all_models(self) -> list[ModelMetadata]:
        return list(self.models.values())

    def get_model(self, model_id: str) -> ModelMetadata | None:
        return self.models.get(model_id)
