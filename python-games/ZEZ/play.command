#!/bin/bash
# Double-click on macOS, or run ./play.command from any directory.
set -u

fail() {
    printf '\nZEZ could not start: %s\n' "$1" >&2
    printf 'Please fix the problem above, then run play.command again.\n' >&2
    exit 1
}

GAME_ROOT="$(cd -- "$(dirname -- "$0")" && pwd)" || fail "Cannot find the game folder."
cd -- "$GAME_ROOT" || fail "Cannot open the game folder."

if [ ! -x "$GAME_ROOT/.venv/bin/python" ]; then
    if ! command -v python3 >/dev/null 2>&1; then
        fail "Python 3.9 or newer is required. Install Python from https://www.python.org/downloads/."
    fi
    python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || fail "Python 3.9 or newer is required."
    printf 'Preparing the ZEZ environment (first launch only)...\n'
    python3 -m venv "$GAME_ROOT/.venv" || fail "Could not create .venv. Check Python installation and folder permissions."
fi

PYTHON="$GAME_ROOT/.venv/bin/python"
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || fail "The .venv Python is too old. Remove .venv and install Python 3.9 or newer."

# Check locally, so subsequent launches work offline and never contact pip.
if ! "$PYTHON" -c 'import importlib.metadata as m; import pygame; assert m.version("pygame-ce") == "2.5.6"' >/dev/null 2>&1; then
    printf 'Installing game dependencies (internet required on first launch)...\n'
    "$PYTHON" -m pip --disable-pip-version-check install -r "$GAME_ROOT/requirements.txt" || fail "Dependency installation failed. Check your internet connection and retry."
fi

export PYGAME_HIDE_SUPPORT_PROMPT=1
"$PYTHON" "$GAME_ROOT/main.py" "$@"
RESULT=$?
if [ "$RESULT" -ne 0 ]; then
    printf '\nZEZ stopped with error code %s. See the message above.\n' "$RESULT" >&2
fi
exit "$RESULT"
