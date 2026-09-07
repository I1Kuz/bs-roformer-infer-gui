import sys
import os
import json
import argparse
import traceback
from pathlib import Path

# Ensure ffmpeg.exe (which sits next to the python.exe) is in PATH
os.environ["PATH"] += os.pathsep + os.path.dirname(sys.executable)

# Force standard output to be unbuffered (or flush manually)
# We will write all JSON responses to stdout.
# Any random prints from libraries should ideally go to stderr.

def handle_registry():
    import bs_roformer
    from bs_roformer.download import default_models_dir
    import os
    
    registry_list = []
    # Try to fetch models
    mdir = default_models_dir()
    for category in bs_roformer.MODEL_REGISTRY.categories():
        models = bs_roformer.MODEL_REGISTRY.list(category)
        for model in models:
            # Check if installed
            ckpt_path = mdir / model.slug / model.checkpoint
            is_installed = ckpt_path.exists()
            
            registry_list.append({
                "id": model.slug,
                "name": model.name,
                "category": category,
                "stems": model.default_sources,
                "checkpoint": model.checkpoint,
                "installed": is_installed
            })
    
    print(json.dumps({"status": "success", "data": registry_list}))
    sys.exit(0)

def handle_serve():
    import logging
    import torch
    import yaml
    import numpy as np
    import soundfile as sf
    import re
    from pathlib import Path
    from ml_collections import ConfigDict
    
    from bs_roformer import ensure_model_assets
    from bs_roformer.utils import demix_track, get_model_from_config
    from bs_roformer.inference import SafeLoaderWithTuple

    # Redirect sys.stdout to sys.stderr to prevent libraries from breaking JSON stream
    real_stdout = sys.stdout
    original_stderr = sys.stderr
    
    class ProgressStream:
        def __init__(self, original_stream):
            self.original_stream = original_stream
            self.buf = ""
            self.total_time = None
            
        def write(self, text):
            # Replace \r with \n for the underlying pipe so engine.py's readline() doesn't block and cause a pipe buffer deadlock.
            safe_text = text.replace('\r', '\n')
            self.original_stream.write(safe_text)
            self.original_stream.flush()
            
            self.buf += text
            
            # Extract full lines by \n or \r
            import re
            lines = re.split(r'[\r\n]+', self.buf)
            
            # The last element is the remaining incomplete line
            self.buf = lines[-1]
            
            # Process all complete lines
            for line in lines[:-1]:
                self._parse_line(line.strip())
                
            # If the incomplete line looks like a progress update, parse it and clear it
            # so we don't wait for the next \r
            if self.buf.strip() and ("Estimated" in self.buf or "%" in self.buf):
                self._parse_line(self.buf.strip())
                self.buf = ""
                
        def _parse_line(self, line):
            if not line: return
            m = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
            if m:
                val = float(m.group(1)) / 100.0
                msg = json.dumps({"event": "progress", "payload": {"progress": val, "text": f"{int(val * 100)}%", "type": "download"}})
                real_stdout.write(msg + "\n")
                real_stdout.flush()
            elif "Estimated total processing time" in line:
                m_time = re.search(r'([\d\.]+)\s*seconds', line)
                if m_time:
                    self.total_time = float(m_time.group(1))
                    msg = json.dumps({"event": "progress", "payload": {"progress": 0.0, "text": "Starting...", "type": "transform"}})
                    real_stdout.write(msg + "\n")
                    real_stdout.flush()
            elif "Estimated time remaining" in line:
                m_time = re.search(r'([\d\.]+)\s*seconds', line)
                if m_time and self.total_time and self.total_time > 0:
                    rem = float(m_time.group(1))
                    val = max(0.0, min(1.0, (self.total_time - rem) / self.total_time))
                    
                    time_str = f"{rem:.1f}s left"
                    if rem > 60:
                        mins = int(rem // 60)
                        secs = int(rem % 60)
                        time_str = f"{mins}m {secs}s left"
                        
                    msg = json.dumps({"event": "progress", "payload": {"progress": val, "text": time_str, "type": "transform"}})
                    real_stdout.write(msg + "\n")
                    real_stdout.flush()
            elif "Estimated" in line or "processing" in line:
                msg = json.dumps({"event": "progress_text", "payload": {"text": line}})
                real_stdout.write(msg + "\n")
                real_stdout.flush()

        def flush(self):
            self.original_stream.flush()

    class SafeModelWrapper(torch.nn.Module):
        """Ensures the model output tensor along time dimension matches the input chunk length."""
        def __init__(self, inner):
            super().__init__()
            self._inner = inner
            
        def forward(self, part, *args, **kwargs):
            expected_len = part.shape[-1]
            out = self._inner(part, *args, **kwargs)
            if isinstance(out, (list, tuple)):
                res = out[0]
                if torch.is_tensor(res):
                    if res.shape[-1] < expected_len:
                        res = torch.nn.functional.pad(res, (0, expected_len - res.shape[-1]))
                    elif res.shape[-1] > expected_len:
                        res = res[..., :expected_len]
                return (res, *out[1:])
            elif torch.is_tensor(out):
                if out.shape[-1] < expected_len:
                    out = torch.nn.functional.pad(out, (0, expected_len - out.shape[-1]))
                elif out.shape[-1] > expected_len:
                    out = out[..., :expected_len]
                return out
            return out
            
        def __getattr__(self, name):
            try:
                return super().__getattr__(name)
            except AttributeError:
                return getattr(self._inner, name)

    sys.stdout = ProgressStream(original_stderr)
    sys.stderr = sys.stdout
    
    session_state = {}
    
    def send_event(event_type: str, payload: dict):
        msg = json.dumps({"event": event_type, "payload": payload})
        real_stdout.write(msg + "\n")
        real_stdout.flush()

    # Setup basic logging to stderr
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
            
        cmd = req.get("command")
        req_id = req.get("id")
        
        if cmd == "load":
            model_id = req.get("model_id")
            device = req.get("device", "auto")
            vram_limit = req.get("vram_limit", 0)
            
            try:
                import torch
                
                # Apply VRAM limit if requested
                if vram_limit > 0 and torch.cuda.is_available():
                    total_memory = torch.cuda.get_device_properties(0).total_memory
                    limit_bytes = vram_limit * 1024 * 1024 * 1024
                    if limit_bytes < total_memory:
                        try:
                            torch.cuda.set_per_process_memory_fraction(limit_bytes / total_memory, 0)
                            logging.info(f"Set VRAM limit to {vram_limit}GB")
                        except Exception as e:
                            logging.error(f"Failed to set VRAM limit: {e}")
                            
                send_event("model_loading", {"model_id": model_id})
                
                ckpt_path, config_path = ensure_model_assets(model_id)
                
                with open(config_path) as f:
                    config = ConfigDict(yaml.load(f, Loader=SafeLoaderWithTuple))
                
                # Assume standard bs_roformer for model_type
                model = get_model_from_config("bs_roformer", config)
                
                try:
                    model.load_state_dict(torch.load(ckpt_path, map_location=torch.device("cpu"), weights_only=False))
                except Exception as load_err:
                    err_str = str(load_err).lower()
                    if "zip archive" in err_str or "corrupt" in err_str or "invalid" in err_str:
                        import os
                        try:
                            os.remove(ckpt_path)
                        except:
                            pass
                        raise RuntimeError("Model file was corrupted (e.g. from an interrupted download) and has been automatically deleted. Please start the transform again to re-download.")
                    raise load_err
                
                if device == "auto" or not device:
                    if torch.cuda.is_available():
                        torch_device = torch.device("cuda:0")
                    else:
                        torch_device = torch.device("cpu")
                else:
                    torch_device = torch.device(device)
                    
                model = model.to(torch_device)
                model.eval()
                
                session_state['model'] = model
                session_state['config'] = config
                session_state['device'] = torch_device
                session_state['vram_limit'] = vram_limit
                
                send_event("model_loaded", {"model_id": model_id, "status": "success"})
                real_stdout.write(json.dumps({"id": req_id, "status": "success"}) + "\n")
                real_stdout.flush()
                
            except Exception as e:
                err_msg = str(e)
                logging.error(traceback.format_exc())
                send_event("model_loaded", {"model_id": model_id, "status": "error", "error": err_msg})
                real_stdout.write(json.dumps({"id": req_id, "status": "error", "error": err_msg}) + "\n")
                real_stdout.flush()

        elif cmd == "infer":
            import logging
            logging.error(f"Received INFER command with req: {req}")
            
            input_file = Path(req.get("input_file"))
            store_dir = Path(req.get("store_dir"))
            
            chunk_preset = req.get("chunk_size_preset", "Auto")
            overlap = int(req.get("overlap", 4))
            export_format = req.get("export_format", "WAV 32-bit (Float)")
            
            model = session_state.get('model')
            config = session_state.get('config')
            torch_device = session_state.get('device')
            
            if not model:
                real_stdout.write(json.dumps({"id": req_id, "status": "error", "error": "No model loaded"}) + "\n")
                real_stdout.flush()
                continue
                
            # --- Apply config overrides ---
            import torch
            
            # 1. Determine STFT hop length to ensure chunk_size is an exact multiple
            hop = 512
            if hasattr(config, 'model') and hasattr(config.model, 'stft_hop_length'):
                hop = config.model.stft_hop_length
            elif hasattr(config, 'audio') and hasattr(config.audio, 'hop_length'):
                hop = config.audio.hop_length
            elif hasattr(config, 'model') and hasattr(config.model, 'hop_length'):
                hop = config.model.hop_length
            elif hasattr(config, 'inference') and hasattr(config.inference, 'hop_length'):
                hop = config.inference.hop_length

            # 2. Get native model chunk size from config (defaults to 588800 = 1150 * 512 for BS-RoFormer)
            native_chunk = 588800
            if hasattr(config, 'inference') and hasattr(config.inference, 'chunk_size') and config.inference.chunk_size:
                native_chunk = config.inference.chunk_size
            elif hasattr(config, 'audio') and hasattr(config.audio, 'chunk_size') and config.audio.chunk_size:
                native_chunk = config.audio.chunk_size
            native_chunk = (native_chunk // hop) * hop

            # 3. Resolve chunk size based on preset
            if chunk_preset.startswith("Small"):
                chunk_size = (352800 // hop) * hop
            elif chunk_preset.startswith("Medium"):
                chunk_size = (470400 // hop) * hop
            elif chunk_preset.startswith("Big"):
                chunk_size = native_chunk
            elif chunk_preset.startswith("Huge"):
                chunk_size = (705600 // hop) * hop
            elif chunk_preset == "Auto":
                # By default, use native chunk size (588800) for highest separation quality
                chunk_size = native_chunk
                
                # Only downscale if GPU VRAM is low (< 5.5 GB) to prevent OOM
                if torch.cuda.is_available():
                    total_memory = torch.cuda.get_device_properties(0).total_memory
                    gb = total_memory / (1024 ** 3)
                    vram_lim = session_state.get('vram_limit', 0)
                    if vram_lim > 0 and vram_lim < gb:
                        gb = float(vram_lim)
                        
                    if gb < 4.0:
                        chunk_size = (352800 // hop) * hop
                    elif gb < 5.5:
                        chunk_size = (470400 // hop) * hop
            else:
                chunk_size = native_chunk

            if hasattr(config, 'inference'):
                config.inference.chunk_size = chunk_size
                config.inference.num_overlap = overlap
                if hasattr(config.inference, 'dim_t') and hop:
                    config.inference.dim_t = chunk_size // hop
                    
            if hasattr(config, 'audio'):
                config.audio.chunk_size = chunk_size
                if hasattr(config.audio, 'dim_t') and hop:
                    config.audio.dim_t = chunk_size // hop
                if hasattr(config.audio, 'num_overlap'):
                    config.audio.num_overlap = overlap
            # ------------------------------
                
            try:
                send_event("infer_start", {"input_file": str(input_file)})
                
                # Emit explicit text so user knows we are busy loading audio
                send_event("progress_text", {"text": f"Loading audio {input_file.name} into memory..."})
                
                store_dir.mkdir(parents=True, exist_ok=True)
                
                mix, sr = sf.read(input_file)
                original_mono = False
                if len(mix.shape) == 1:
                    original_mono = True
                    mix = np.stack([mix, mix], axis=-1)
                    
                mixture = torch.tensor(mix.T, dtype=torch.float32)
                
                safe_model = SafeModelWrapper(model)
                res, _ = demix_track(config, safe_model, mixture, torch_device, None)
                
                instruments = config.training.instruments
                if getattr(config.training, "target_instrument", None) is not None:
                    instruments = [config.training.target_instrument]
                    
                import subprocess
                import os
                def save_track(data, name_suffix):
                    out_path = store_dir / f"{input_file.stem}_{name_suffix}"
                    fmt = export_format.upper()
                    if "MP3" in fmt:
                        temp_wav = out_path.with_suffix('.temp.wav')
                        sf.write(temp_wav, data, sr, subtype="FLOAT")
                        subprocess.run(["ffmpeg", "-y", "-i", str(temp_wav), "-b:a", "320k", str(out_path.with_suffix(".mp3"))], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        os.remove(temp_wav)
                    elif "FLAC" in fmt:
                        sf.write(out_path.with_suffix(".flac"), data, sr, format="FLAC")
                    elif "16-BIT" in fmt:
                        sf.write(out_path.with_suffix(".wav"), data, sr, subtype="PCM_16")
                    elif "24-BIT" in fmt:
                        sf.write(out_path.with_suffix(".wav"), data, sr, subtype="PCM_24")
                    else:
                        sf.write(out_path.with_suffix(".wav"), data, sr, subtype="FLOAT")
                    
                for instr in instruments:
                    vocals_output = res[instr].T
                    if original_mono:
                        vocals_output = vocals_output[:, 0]
                    save_track(vocals_output, instr)
                    
                if instruments:
                    vocals_output = res[instruments[0]].T
                    if original_mono:
                        vocals_output = vocals_output[:, 0]
                    instrumental = mix - vocals_output
                    save_track(instrumental, "instrumental")
                
                send_event("infer_done", {"input_file": str(input_file), "status": "success"})
                real_stdout.write(json.dumps({"id": req_id, "status": "success"}) + "\n")
                real_stdout.flush()
            except Exception as e:
                err_msg = str(e)
                logging.error(traceback.format_exc())
                send_event("infer_done", {"input_file": str(input_file), "status": "error", "error": err_msg})
                real_stdout.write(json.dumps({"id": req_id, "status": "error", "error": err_msg}) + "\n")
                real_stdout.flush()
                
        elif cmd == "release":
            session_state.clear()
            # Clear CUDA cache if applicable
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass
            real_stdout.write(json.dumps({"id": req_id, "status": "success"}) + "\n")
            real_stdout.flush()
            
        elif cmd == "exit":
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", action="store_true", help="Print registry as JSON")
    parser.add_argument("--serve", action="store_true", help="Start RPC server")
    
    args = parser.parse_args()
    
    if args.registry:
        handle_registry()
    elif args.serve:
        handle_serve()
    else:
        print(json.dumps({"error": "No action specified"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
