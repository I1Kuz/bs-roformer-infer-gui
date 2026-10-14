import json
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import cast, final

from app.core.logging import get_logger
from app.core.paths import get_python_exe

logger = get_logger(__name__)


# any chance to type it?
_DETECT_SCRIPT = textwrap.dedent("""\
    import json
    import torch

    info = {"cuda_available": torch.cuda.is_available(), "gpu_name": "Unknown", "vram_gb": 0.0}
    if info["cuda_available"]:
        try:
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["vram_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except Exception:
            pass
    print(json.dumps(info))
""")


@dataclass(slots=True)
class HardwareInfo:
    cuda_available: bool = False
    gpu_name: str = "Unknown"
    vram_gb: float = 0.0


@final
class HardwareDetector:
    def __init__(self) -> None:
        self.python_exe: Path = get_python_exe()
        self.info: HardwareInfo = HardwareInfo()

    @property
    def cuda_available(self) -> bool:
        return self.info.cuda_available

    @property
    def gpu_name(self) -> str:
        return self.info.gpu_name

    @property
    def vram_gb(self) -> float:
        return self.info.vram_gb

    def detect(self) -> HardwareInfo:
        if not self.python_exe.exists():
            logger.warning("Python runtime not found. Cannot detect PyTorch hardware.")
            return self.info

        try:
            result = subprocess.run(
                [str(self.python_exe), "-c", _DETECT_SCRIPT],
                capture_output=True,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                raw: object = json.loads(result.stdout.strip())
                if isinstance(raw, dict):
                    data = cast(dict[str, object], raw)
                    self.info = HardwareInfo(
                        cuda_available=bool(data.get("cuda_available", False)),
                        gpu_name=str(data.get("gpu_name", "Unknown")),
                        vram_gb=float(data.get("vram_gb", 0.0)),  # type: ignore[arg-type]
                    )
                logger.info(
                    "Hardware detected: CUDA=%s, GPU=%s, VRAM=%.1f GB",
                    self.info.cuda_available,
                    self.info.gpu_name,
                    self.info.vram_gb,
                )
            else:
                logger.error(
                    "Hardware detection process failed with code %d: %s",
                    result.returncode,
                    result.stderr.strip(),
                )
        except Exception as e:
            logger.error("Error executing hardware detection: %s", e)

        return self.info

    def get_display_string(self) -> str:
        from app.core.i18n import get_translations

        t = get_translations()
        if self.info.cuda_available:
            return f"{t.queue.gpu_prefix}{self.info.gpu_name} (VRAM: {self.info.vram_gb:.1f} GB)"
        return t.queue.no_gpu
