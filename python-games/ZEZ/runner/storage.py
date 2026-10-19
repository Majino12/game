"""Small, versioned user saves; importing this module does not require pygame."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import List, Optional, Union
from uuid import uuid4


costs = {"beige": 0, "pink": 100, "purple": 250}
COSTS = costs
SAVE_VERSION = 1
PathLike = Union[str, os.PathLike]


@dataclass
class SaveData:
    best_score: int = 0
    best_distance: int = 0
    total_coins: int = 0
    runs: int = 0
    selected: str = "beige"
    unlocked: List[str] = field(default_factory=lambda: ["beige"])
    muted: bool = False
    language: str = "zh"


def save_path() -> Path:
    """Return a per-user location, independent of the game's working directory."""
    override = os.environ.get("ZEZ_SAVE_DIR")
    if override:
        directory = Path(override).expanduser()
    elif sys.platform == "darwin":
        directory = Path.home() / "Library" / "Application Support" / "ZEZ"
    elif sys.platform == "win32":
        directory = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "ZEZ"
    else:
        directory = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "zez"
    return directory / "save.json"


def _validated(payload: object) -> SaveData:
    if not isinstance(payload, dict):
        raise ValueError("Save must be a JSON object")
    version = payload.get("version", SAVE_VERSION)
    if type(version) is not int or version != SAVE_VERSION:
        raise ValueError("Unsupported save version")
    result = SaveData()
    for name in ("best_score", "best_distance", "total_coins", "runs"):
        value = payload.get(name, 0)
        # bool is an int subclass, but is never a legitimate score or balance.
        if type(value) is not int or value < 0:
            raise ValueError("Invalid numeric field: " + name)
        setattr(result, name, value)
    unlocked = payload.get("unlocked", ["beige"])
    if not isinstance(unlocked, list) or any(type(color) is not str or color not in costs for color in unlocked):
        raise ValueError("Invalid unlocked characters")
    result.unlocked = list(dict.fromkeys(["beige"] + unlocked))
    selected = payload.get("selected", "beige")
    if type(selected) is not str or selected not in costs:
        raise ValueError("Invalid selected character")
    result.selected = selected if selected in result.unlocked else "beige"
    result.muted = payload.get("muted", False)
    if type(result.muted) is not bool:
        raise ValueError("Invalid sound setting")
    result.language = payload.get("language", "zh")
    if result.language not in ("zh", "en"):
        raise ValueError("Invalid language setting")
    return result


def _backup_corrupt(path: Path) -> None:
    """Keep the original in place and make a recoverable copy when possible."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(path.name + ".corrupt-" + stamp + "-" + uuid4().hex[:8])
    try:
        shutil.copy2(path, backup)
    except OSError:
        # Read-only directories must not prevent playing with default settings.
        pass


def load_save(path: Optional[PathLike] = None) -> SaveData:
    target = Path(path) if path is not None else save_path()
    try:
        with target.open("r", encoding="utf-8") as stream:
            return _validated(json.load(stream))
    except FileNotFoundError:
        return SaveData()
    except (ValueError, TypeError, UnicodeError):
        _backup_corrupt(target)
        return SaveData()
    except OSError:
        return SaveData()


def save_data(data: SaveData, path: Optional[PathLike] = None) -> bool:
    """Atomically replace a save; return False rather than interrupting gameplay."""
    temporary = None
    try:
        target = Path(path) if path is not None else save_path()
        payload = asdict(data)
        payload["version"] = SAVE_VERSION
        validated = _validated(payload)
        payload = {"version": SAVE_VERSION, **asdict(validated)}
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=str(target.parent),
                                         prefix="." + target.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temporary), str(target))
        temporary = None
        return True
    except (OSError, ValueError, TypeError):
        return False
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass


def purchase(data: SaveData, color: str) -> bool:
    """Unlock and select a character, charging only on the first purchase."""
    if color not in costs:
        return False
    if color in data.unlocked:
        data.selected = color
        return True
    price = costs[color]
    if type(data.total_coins) is not int or data.total_coins < price:
        return False
    data.total_coins -= price
    data.unlocked.append(color)
    data.selected = color
    return True
