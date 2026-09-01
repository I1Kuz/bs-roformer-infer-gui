import subprocess
import json
from app.core.paths import get_runtime_dir
from app.core.logging import get_logger

logger = get_logger(__name__)

class HardwareDetector:
    def __init__(self):
        self.python_exe = get_runtime_dir() / "python.exe"
        self.cuda_available = False
        self.gpu_name = "Unknown"
        self.vram_gb = 0.0

    def detect(self):
        if not self.python_exe.exists():
            logger.warning("Python runtime not found. Cannot detect PyTorch hardware.")
            return

        script = """
import torch
info = {
    'cuda_available': torch.cuda.is_available(),
    'gpu_name': 'Unknown',
    'vram_gb': 0.0
}
if info['cuda_available']:
    try:
        info['gpu_name'] = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory
        info['vram_gb'] = vram / (1024**3)
    except Exception:
        pass
import json
print(json.dumps(info))
"""
        try:
            result = subprocess.run(
                [str(self.python_exe), "-c", script],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                data = json.loads(result.stdout.strip())
                self.cuda_available = data.get('cuda_available', False)
                self.gpu_name = data.get('gpu_name', 'Unknown')
                self.vram_gb = data.get('vram_gb', 0.0)
                logger.info(f"Hardware detected: CUDA={self.cuda_available}, GPU={self.gpu_name}, VRAM={self.vram_gb:.1f}GB")
            else:
                logger.error(f"Hardware detection failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running hardware detection: {e}")

    def get_display_string(self) -> str:
        if self.cuda_available:
            return f"GPU: {self.gpu_name} (VRAM: {self.vram_gb:.1f} GB)"
        else:
            return "GPU: CPU Only (CUDA not available)"
