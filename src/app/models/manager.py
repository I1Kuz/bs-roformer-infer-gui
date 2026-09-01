from pathlib import Path
import json
import subprocess
from dataclasses import dataclass
from app.core.paths import get_runtime_dir, get_worker_script_path
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ModelMetadata:
    id: str
    name: str
    category: str
    stems: list[str]
    checkpoint: str
    installed: bool = False

class ModelManager:
    def __init__(self):
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
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout.strip())
                if data.get("status") == "success":
                    self.models.clear()
                    for item in data.get("data", []):
                        # The worker script doesn't check 'installed' status easily, 
                        # but we can check if the checkpoint file exists in the models cache dir
                        # Actually, bs-roformer-infer handles download path internally.
                        # For now, we assume installed = False and we can add a check later if needed
                        
                        name_str = item["name"]
                        if name_str.startswith("Roformer Model: "):
                            name_str = name_str.replace("Roformer Model: ", "")
                            
                        meta = ModelMetadata(
                            id=item["id"],
                            name=name_str,
                            category=item["category"],
                            stems=item["stems"],
                            checkpoint=item["checkpoint"],
                            installed=item.get("installed", False)
                        )
                        self.models[meta.id] = meta
                    logger.info(f"Loaded {len(self.models)} models from registry.")
                    return True
            else:
                logger.error(f"Failed to fetch registry: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error fetching registry: {e}")
            return False
        return False

    def get_all_models(self) -> list[ModelMetadata]:
        return list(self.models.values())
        
    def get_model(self, model_id: str) -> ModelMetadata:
        return self.models.get(model_id)
