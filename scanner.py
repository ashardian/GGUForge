# =============================================================================
# scanner.py — GGUForge GGUF Model Scanner
# Recursively walks the filesystem to locate .gguf model files,
# reporting their path and size for informed selection.
# =============================================================================

import os
from config import MODEL_EXTENSION, SKIP_DIRS
from logger import log


def _human_size(num_bytes: int) -> str:
    """Convert bytes to a human-readable string (KB / MB / GB)."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def find_gguf_models(start_paths: list) -> list[dict]:
    """
    Walks each path in start_paths, skipping SKIP_DIRS.
    Returns a list of dicts:
        { 'path': str, 'name': str, 'size': str, 'size_bytes': int }
    sorted by size descending (largest models first).
    """
    models = []

    for base_path in start_paths:
        if not os.path.exists(base_path):
            continue

        for root, dirs, files in os.walk(base_path, followlinks=False):
            # Prune skip dirs in-place so os.walk doesn't descend into them
            dirs[:] = [
                d for d in dirs
                if not any(
                    os.path.join(root, d).startswith(skip)
                    for skip in SKIP_DIRS
                )
            ]

            for file in files:
                if not file.endswith(MODEL_EXTENSION):
                    continue
                full_path = os.path.join(root, file)
                try:
                    size_bytes = os.path.getsize(full_path)
                    models.append({
                        "path":       full_path,
                        "name":       file,
                        "size":       _human_size(size_bytes),
                        "size_bytes": size_bytes,
                    })
                except (PermissionError, OSError):
                    continue

    # Sort by size descending — largest (most capable) models first
    models.sort(key=lambda m: m["size_bytes"], reverse=True)
    log("info", f"GGUF scan found {len(models)} model(s) in {start_paths}")
    return models
