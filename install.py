#!/usr/bin/env python3
"""LifeOS Lite installer: one profile in Hermes, one folder of notes.

Works the same on macOS, Linux and Windows. Needs only Python 3.8+ and a
working `hermes` command. Run `python3 install.py --help` for the options.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

HERE = Path(__file__).resolve().parent


def say(text: str = "") -> None:
    print(text, flush=True)


def fail(text: str) -> NoReturn:
    print(f"ОШИБКА: {text}", file=sys.stderr)
    sys.exit(1)


def run_hermes(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    exe = shutil.which("hermes")
    if exe is None:
        fail("команда hermes не найдена. Открой новое окно терминала и проверь, что `hermes --version` работает.")
    result = subprocess.run(
        [exe, *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if check and result.returncode != 0:
        fail(f"`hermes {' '.join(args)}` завершилась с ошибкой:\n{result.stdout}{result.stderr}")
    return result


def default_vault() -> Path:
    """~/Documents/LifeOS when Documents exists (macOS, Windows, most Linux), else ~/LifeOS."""
    home = Path.home()
    documents = home / "Documents"
    return (documents if documents.is_dir() else home) / "LifeOS"


def profile_exists(name: str) -> bool:
    listing = run_hermes("profile", "list").stdout
    return re.search(rf"(?m)^\W*{re.escape(name)}\b", listing) is not None


def profile_dir(name: str) -> Path:
    shown = run_hermes("profile", "show", name).stdout
    match = re.search(r"(?m)^Path:\s+(.+?)\s*$", shown)
    if match and Path(match.group(1)).is_dir():
        return Path(match.group(1))
    # Fallback when `profile show` has another format: HERMES_HOME, then the default home.
    root = os.environ.get("HERMES_HOME")
    base = Path(root) if root else Path.home() / ".hermes"
    candidate = base / "profiles" / name
    if candidate.is_dir():
        return candidate
    fail(f"не нашёл папку профиля. Вывод `hermes profile show {name}`:\n{shown}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Установка профиля LifeOS Lite в Hermes.")
    parser.add_argument("--profile", default="lifeos", help="имя профиля Hermes (по умолчанию lifeos)")
    parser.add_argument("--vault", type=Path, default=None, help="папка заметок (по умолчанию ~/Documents/LifeOS)")
    parser.add_argument("--dry-run", action="store_true", help="показать, что будет сделано, ничего не меняя")
    args = parser.parse_args()

    name = args.profile
    vault = (args.vault or default_vault()).expanduser().resolve()
    template = HERE / "vault" / "LifeOS"
    soul_src = HERE / "profile" / "SOUL.md"
    skills_src = HERE / "profile" / "skills" / "lifeos"
    for path in (template, soul_src, skills_src):
        if not path.exists():
            fail(f"в папке установщика нет {path.relative_to(HERE)}. Распакуй архив целиком.")

    say("== LifeOS Lite: установка ==")
    if shutil.which("hermes") is None:
        fail("команда hermes не найдена. Открой новое окно терминала и проверь, что `hermes --version` работает.")
    if profile_exists(name):
        fail(f"профиль '{name}' уже есть. Запусти с другим именем: python3 install.py --profile {name}2")

    if args.dry_run:
        say(f"Создал бы профиль '{name}' (hermes profile create {name} --clone)")
        say(f"Заметки: {vault} ({'уже есть, не трогаю' if vault.exists() else 'будет создана'})")
        say("Положил бы SOUL.md, навыки lifeos и очистил память профиля.")
        return

    say(f"Создаю профиль '{name}' (модель и ключи берутся из текущего профиля Hermes)...")
    run_hermes("profile", "create", name, "--clone", check=True)
    target = profile_dir(name)
    say(f"Профиль: {target}")

    if vault.exists():
        say(f"Папка заметок уже есть, не трогаю: {vault}")
    else:
        shutil.copytree(template, vault)
        say(f"Папка заметок создана: {vault}")

    soul = soul_src.read_text(encoding="utf-8").replace("{{VAULT}}", str(vault))
    with open(target / "SOUL.md", "w", encoding="utf-8", newline="\n") as handle:
        handle.write(soul)

    skills_dst = target / "skills" / "lifeos"
    shutil.copytree(skills_src, skills_dst, dirs_exist_ok=True)

    memories = target / "memories"
    memories.mkdir(parents=True, exist_ok=True)
    for filename in ("MEMORY.md", "USER.md"):
        (memories / filename).write_text("", encoding="utf-8")

    say()
    say("Готово.")
    say(f"Запуск ассистента:  hermes -p {name}")
    say(f"  (или в приложении Hermes выбери профиль '{name}')")
    say("Первое сообщение:   Давай познакомимся")
    say(f"Заметки можно открыть в Obsidian: Open folder as vault -> {vault}")


if __name__ == "__main__":
    main()
