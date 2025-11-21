import json
import os
from pathlib import Path
from typing import Dict, Union

PathLike = Union[str, Path]


def write_credentials(path: PathLike, data: Dict) -> Path:
    """
    Write captured credentials to disk with restrictive permissions.
    """
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    try:
        target.chmod(0o600)
    except PermissionError:
        # Best-effort; on some platforms chmod may fail.
        pass

    return target
