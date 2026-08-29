# Built-in Dependencies
from __future__ import annotations
import argparse
import platform
import secrets
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
ENV_PATH = BACKEND_DIR / ".env"
ENV_EXAMPLE_PATH = BACKEND_DIR / ".env.example"
LOCUST_DIR = ROOT_DIR / "locust"
OPERATING_SYSTEM = platform.system()

REQUIRED_ENV_KEYS = (
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_SERVER",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "REDIS_CACHE_HOST",
    "REDIS_CACHE_PORT",
    "REDIS_CACHE_PASSWORD",
    "USER_FIRST_ADMIN_NAME",
    "USER_FIRST_ADMIN_EMAIL",
    "USER_FIRST_ADMIN_USERNAME",
    "USER_FIRST_ADMIN_PASSWORD",
)

WIZARD_KEYS = (
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_SERVER",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "REDIS_CACHE_HOST",
    "REDIS_CACHE_PORT",
    "REDIS_CACHE_USERNAME",
    "REDIS_CACHE_PASSWORD",
    "USER_FIRST_ADMIN_NAME",
    "USER_FIRST_ADMIN_EMAIL",
    "USER_FIRST_ADMIN_USERNAME",
    "USER_FIRST_ADMIN_PASSWORD",
)

FLOWER_DEFAULT_AUTH = "admin:changeme"


def print_color(color: str, text: str) -> None:
    colors = {
        "RED": "\033[1;31m",
        "GREEN": "\033[0;32m",
        "YELLOW": "\033[1;33m",
        "BLUE": "\033[1;34m",
        "RESET": "\033[0m",
    }
    print(f"{colors[color]}{text}{colors['RESET']}")


def read_color(prompt: str) -> str:
    return input(f"\033[1;37m{prompt}\033[0m")


def print_banner() -> None:
    print_color("YELLOW", "#########################################################################################################################")
    print_color("YELLOW", "######################################### FastAPI Async SQLModel Starter (Setup) ########################################")
    print_color("YELLOW", "#########################################################################################################################")
    print_color("GREEN", "Supercharge your FastAPI development. A backend for perfectionists with deadlines and lovers of asynchronous programming.")


def check_dependencies() -> str:
    python_path: str | None = None
    if OPERATING_SYSTEM == "Windows":
        python_version_check = (
            "import sys; "
            "print(sys.executable); "
            "sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)"
        )
        python_commands = [
            ["py", "-3.11", "-c", python_version_check],
            ["python", "-c", python_version_check],
        ]
        for command in python_commands:
            try:
                python_check = subprocess.run(command, capture_output=True, text=True)
            except FileNotFoundError:
                continue
            if python_check.returncode == 0 and python_check.stdout.strip():
                python_path = python_check.stdout.strip()
                break
        python_installed = python_path is not None
    else:
        try:
            python_installed = (
                subprocess.run(
                    ["python3.11", "-V"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ).returncode
                == 0
            )
        except FileNotFoundError:
            python_installed = False
        python_path = (
            subprocess.run(["which", "python3.11"], capture_output=True, text=True).stdout.strip()
            if python_installed
            else None
        )

    try:
        poetry_installed = (
            subprocess.run(
                ["poetry", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
    except FileNotFoundError:
        poetry_installed = False

    missing: list[str] = []
    if not python_installed or not python_path:
        missing.append("Python 3.11")
    if not poetry_installed:
        missing.append("Poetry")
    if missing:
        print_color(
            "RED",
            f"\nError: missing required dependencies: {', '.join(missing)}. "
            "Please install them before running this setup.",
        )
        sys.exit(1)
    return python_path


def run_command(
    args: list[str],
    *,
    cwd: Path,
    check: bool = False,
) -> int:
    result = subprocess.run(args, cwd=str(cwd))
    if check and result.returncode != 0:
        print_color("RED", f"\nCommand failed with exit code {result.returncode}.\n")
    return result.returncode


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_value(key: str) -> str:
    return parse_env_file(ENV_PATH).get(key, "")


def set_env_values(updates: dict[str, str]) -> None:
    if ENV_PATH.is_file():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    else:
        lines = []
    remaining = dict(updates)
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in remaining:
                new_lines.append(_format_env_line(key, remaining.pop(key)))
                continue
        new_lines.append(line)
    if remaining:
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        for key, value in remaining.items():
            new_lines.append(_format_env_line(key, value))
    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _format_env_line(key: str, value: str) -> str:
    if (
        value == ""
        or value.lower() in {"true", "false"}
        or value.replace(".", "", 1).replace("-", "", 1).isdigit()
    ):
        return f"{key}={value}"
    escaped = value.replace('"', '\\"')
    return f'{key}="{escaped}"'


def env_needs_setup() -> bool:
    if not ENV_PATH.is_file():
        return True
    values = parse_env_file(ENV_PATH)
    return any(not values.get(key) for key in REQUIRED_ENV_KEYS)


def ensure_env() -> None:
    if not ENV_PATH.is_file():
        if not ENV_EXAMPLE_PATH.is_file():
            print_color("RED", f"\nMissing {ENV_EXAMPLE_PATH}. Cannot create .env.\n")
            sys.exit(1)
        shutil.copy2(ENV_EXAMPLE_PATH, ENV_PATH)
        print_color("GREEN", "\nCopied 'backend/.env.example' to 'backend/.env'.")
    if not env_value("SECRET_KEY"):
        set_env_values({"SECRET_KEY": secrets.token_urlsafe(32)})
        print_color("GREEN", "Generated SECRET_KEY in 'backend/.env'.")


def ensure_flower_auth() -> None:
    if not env_value("FLOWER_BASIC_AUTH"):
        set_env_values({"FLOWER_BASIC_AUTH": FLOWER_DEFAULT_AUTH})
        print_color(
            "GREEN",
            f"Set FLOWER_BASIC_AUTH={FLOWER_DEFAULT_AUTH} in 'backend/.env' (local default).",
        )


def prompt_with_default(name: str, current: str) -> str:
    entered = read_color(f"{name} [{current}]: ").strip()
    return entered if entered else current


def run_env_wizard() -> None:
    print_color(
        "BLUE",
        "\nConfirm local environment values. Press ENTER to keep the value in brackets.\n",
    )
    values = parse_env_file(ENV_PATH)
    updates: dict[str, str] = {}
    for key in WIZARD_KEYS:
        updates[key] = prompt_with_default(key, values.get(key, ""))
    cache_host = updates.get("REDIS_CACHE_HOST", values.get("REDIS_CACHE_HOST", ""))
    cache_port = updates.get("REDIS_CACHE_PORT", values.get("REDIS_CACHE_PORT", "6379"))
    cache_username = updates.get("REDIS_CACHE_USERNAME", values.get("REDIS_CACHE_USERNAME", ""))
    cache_password = updates.get("REDIS_CACHE_PASSWORD", values.get("REDIS_CACHE_PASSWORD", ""))
    cache_ssl = values.get("REDIS_CACHE_USE_SSL", "False")
    for prefix in ("REDIS_BROKER", "REDIS_RATE_LIMIT"):
        updates[f"{prefix}_HOST"] = cache_host
        updates[f"{prefix}_PORT"] = cache_port
        updates[f"{prefix}_USERNAME"] = cache_username
        updates[f"{prefix}_PASSWORD"] = cache_password
        updates[f"{prefix}_USE_SSL"] = cache_ssl
    set_env_values(updates)
    print_color("GREEN", "\nUpdated 'backend/.env'.")


def ensure_poetry(
    python_path: str, cwd: Path = BACKEND_DIR, *, force_install: bool = False
) -> bool:
    if run_command(["poetry", "env", "use", python_path], cwd=cwd, check=True) != 0:
        return False
    return run_command(["poetry", "install"], cwd=cwd, check=True) == 0


def poetry_run(args: list[str], *, cwd: Path = BACKEND_DIR, check: bool = False) -> int:
    return run_command(["poetry", "run", *args], cwd=cwd, check=check)


def alembic_upgrade() -> bool:
    print_color("GREEN", "\nRunning Alembic migrations...\n")
    return poetry_run(["alembic", "upgrade", "head"], check=True) == 0


def prepare_backend(python_path: str, *, migrate: bool = True) -> bool:
    if not ensure_poetry(python_path):
        return False
    ensure_env()
    if env_needs_setup():
        print_color(
            "YELLOW",
            "\nbackend/.env is missing required values. Use 'Setup environment' first.\n",
        )
        return False
    if migrate and not alembic_upgrade():
        return False
    return True


def setup_environment(python_path: str) -> None:
    print_color("RED", "\n-> Setup environment...\n")
    if not ensure_poetry(python_path, force_install=True):
        return
    ensure_env()
    run_env_wizard()
    if env_needs_setup():
        print_color("YELLOW", "\nSome required values are still empty. Edit backend/.env.\n")
        return
    alembic_upgrade()
    print_color("GREEN", "\n-> Environment setup complete.\n")


def start_fastapi(python_path: str) -> None:
    if not prepare_backend(python_path):
        return
    print_color(
        "RED",
        f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] -> Starting the FastAPI server...\n",
    )
    web_concurrency = env_value("WEB_CONCURRENCY")
    if not web_concurrency.isdigit() or int(web_concurrency) == 1:
        poetry_run(
            [
                "uvicorn",
                "src.main:app",
                "--reload",
                "--reload-delay",
                "0.25",
                "--reload-include",
                "*.py",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--timeout-keep-alive",
                "5",
            ]
        )
    else:
        poetry_run(
            [
                "uvicorn",
                "src.main:app",
                "--workers",
                web_concurrency,
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ]
        )
    print_color("RED", "\n-> Stopping the FastAPI server...\n")


def start_celery_worker(python_path: str) -> None:
    if not prepare_backend(python_path):
        return
    print_color("RED", "\n-> Running the Celery worker...\n")
    args = ["celery", "-A", "src.worker", "worker", "--loglevel=info"]
    if OPERATING_SYSTEM == "Windows":
        args.extend(["-P", "threads"])
    poetry_run(args)
    print_color("RED", "\n-> Finished running the Celery worker...\n")


def start_celery_beat(python_path: str) -> None:
    if not prepare_backend(python_path):
        return
    print_color("RED", "\n-> Running the Celery beat...\n")
    poetry_run(["celery", "-A", "src.worker", "beat", "--loglevel=info"])
    print_color("RED", "\n-> Finished running the Celery beat...\n")


def start_flower(python_path: str) -> None:
    if not prepare_backend(python_path, migrate=False):
        return
    ensure_flower_auth()
    print_color("RED", "\n-> Running Celery Flower...\n")
    poetry_run(["celery", "-A", "src.worker", "flower", "--loglevel=info"])
    print_color("RED", "\n-> Finished running Celery Flower...\n")


def prompt_choice(options: list[tuple[str, str]]) -> str:
    print_color("BLUE", "Select an option:\n")
    for key, label in options:
        print(f"{key} - {label}")
    return read_color("\nEnter the number corresponding to your choice: ").strip()


def local_menu(python_path: str) -> None:
    while True:
        print_color("BLUE", "\nLocal Development\n")
        options: list[tuple[str, str]] = []
        actions: dict[str, Callable[[], None]] = {}
        next_key = 1
        if env_needs_setup():
            options.append((str(next_key), "Setup environment"))
            actions[str(next_key)] = lambda: setup_environment(python_path)
            next_key += 1
        start_items = [
            ("Start FastAPI server", lambda: start_fastapi(python_path)),
            ("Start Celery worker", lambda: start_celery_worker(python_path)),
            ("Start Celery beat", lambda: start_celery_beat(python_path)),
            ("Start Celery Flower", lambda: start_flower(python_path)),
        ]
        for label, func in start_items:
            options.append((str(next_key), label))
            actions[str(next_key)] = func
            next_key += 1
        back_key = str(next_key)
        options.append((back_key, "Back"))
        choice = prompt_choice(options)
        if choice == back_key:
            return
        action = actions.get(choice)
        if action is None:
            print_color("YELLOW", "\nInvalid choice.\n")
            continue
        action()


def alembic_revision() -> None:
    message = read_color("Revision message: ").strip()
    if not message:
        print_color("YELLOW", "\nRevision message cannot be empty.\n")
        return
    poetry_run(["alembic", "revision", "--autogenerate", "-m", message], check=True)


def migrations_menu(python_path: str) -> None:
    while True:
        print_color("BLUE", "\nDatabase migrations (from backend/)\n")
        choice = prompt_choice(
            [
                ("1", "Alembic upgrade head"),
                ("2", "Alembic revision --autogenerate"),
                ("3", "Alembic current"),
                ("4", "Back"),
            ]
        )
        if choice == "4":
            return
        if not ensure_poetry(python_path):
            continue
        ensure_env()
        if choice == "1":
            alembic_upgrade()
        elif choice == "2":
            alembic_revision()
        elif choice == "3":
            poetry_run(["alembic", "current"], check=True)
        else:
            print_color("YELLOW", "\nInvalid choice.\n")


def tests_menu(python_path: str) -> None:
    while True:
        print_color("BLUE", "\nTests (from backend/)\n")
        choice = prompt_choice(
            [
                ("1", "Unit tests (pytest -m unit)"),
                ("2", "Integration tests (pytest -m integration)"),
                ("3", "Full suite (pytest -v)"),
                ("4", "Coverage gate (80%)"),
                ("5", "Back"),
            ]
        )
        if choice == "5":
            return
        if not ensure_poetry(python_path):
            continue
        commands = {
            "1": ["pytest", "-m", "unit", "-v"],
            "2": ["pytest", "-m", "integration", "-v"],
            "3": ["pytest", "-v"],
            "4": [
                "pytest",
                "-v",
                "--cov",
                "--cov-report=term-missing",
                "--cov-fail-under=80",
            ],
        }
        args = commands.get(choice)
        if args is None:
            print_color("YELLOW", "\nInvalid choice.\n")
            continue
        print_color("RED", "\n-> Running tests...\n")
        poetry_run(args, check=True)
        print_color("RED", "\n-> Finished running tests...\n")


def run_ci_checks(python_path: str) -> None:
    if not ensure_poetry(python_path):
        return
    print_color("RED", "\n-> Running CI checks (ruff format --check, ruff check src, mypy src, pytest -m unit)...\n")
    if poetry_run(["ruff", "format", "--check", "."], check=True) != 0:
        return
    if poetry_run(["ruff", "check", "src"], check=True) != 0:
        return
    if poetry_run(["mypy", "src"], check=True) != 0:
        return
    poetry_run(["pytest", "-m", "unit", "-v"], check=True)
    print_color("RED", "\n-> Finished CI checks...\n")


def tools_menu(python_path: str) -> None:
    while True:
        print_color("BLUE", "\nProject Tools\n")
        choice = prompt_choice(
            [
                ("1", "Database migrations"),
                ("2", "Run tests"),
                ("3", "CI checks (ruff format, ruff check, mypy, unit tests)"),
                ("4", "Format code (ruff format)"),
                ("5", "Type check (mypy src)"),
                ("6", "Format check (ruff format --check)"),
                ("7", "Back"),
            ]
        )
        if choice == "7":
            return
        if choice == "1":
            migrations_menu(python_path)
        elif choice == "2":
            tests_menu(python_path)
        elif choice == "3":
            run_ci_checks(python_path)
        elif choice == "4":
            if ensure_poetry(python_path):
                print_color("RED", "\n-> Formatting with ruff...\n")
                poetry_run(["ruff", "format", "."], check=True)
                print_color("RED", "\n-> Finished formatting...\n")
        elif choice == "5":
            if ensure_poetry(python_path):
                poetry_run(["mypy", "src"], check=True)
        elif choice == "6":
            if ensure_poetry(python_path):
                poetry_run(["ruff", "format", "--check", "."], check=True)
        else:
            print_color("YELLOW", "\nInvalid choice.\n")


def locust_menu(python_path: str) -> None:
    print_color("RED", "\n-> Load Testing (Locust)...\n")
    if not ensure_poetry(python_path, cwd=LOCUST_DIR):
        return
    print_color("GREEN", "\n-> Locust environment ready.\n")
    print_color("BLUE", "Make sure the backend API is running before starting Locust.")
    print_color("BLUE", "Locust reads credentials from 'backend/.env'.\n")
    while True:
        choice = prompt_choice(
            [
                ("1", "Start Locust (Web UI at http://127.0.0.1:8089)"),
                ("2", "Start Locust (headless: 50 users, 10/s, 60s)"),
                ("3", "Back"),
            ]
        )
        if choice == "3":
            return
        if choice == "1":
            print_color(
                "RED",
                f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] -> Starting Locust (Web UI)...\n",
            )
            print_color("GREEN", "Open http://127.0.0.1:8089 in your browser.\n")
            poetry_run(["locust"], cwd=LOCUST_DIR)
            print_color("RED", "\n-> Stopping Locust...\n")
        elif choice == "2":
            print_color(
                "RED",
                f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] -> Starting Locust (headless)...\n",
            )
            poetry_run(
                ["locust", "--headless", "-u", "50", "-r", "10", "--run-time", "60s"],
                cwd=LOCUST_DIR,
            )
            print_color("RED", "\n-> Locust load test finished.\n")
        else:
            print_color("YELLOW", "\nInvalid choice.\n")


def main_menu(python_path: str) -> None:
    while True:
        print_color("BLUE", "\nProject CLI")
        print_color(
            "YELLOW",
            "Production deploy is documented in docs/deploy-guide.md (not this menu).\n",
        )
        choice = prompt_choice(
            [
                ("1", "Local Development"),
                ("2", "Project Tools"),
                ("3", "Load Testing (Locust)"),
                ("4", "Exit"),
            ]
        )
        if choice == "1":
            local_menu(python_path)
        elif choice == "2":
            tools_menu(python_path)
        elif choice == "3":
            locust_menu(python_path)
        elif choice == "4":
            print("\nExiting...\n")
            return
        else:
            print_color("YELLOW", "\nInvalid choice.\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project CLI for local development, tests, migrations, and Locust.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("local", "tools", "locust"),
        help="Skip the top menu and open this submenu (default: interactive main menu).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    python_path = check_dependencies()
    print_banner()
    if args.command == "local":
        local_menu(python_path)
    elif args.command == "tools":
        tools_menu(python_path)
    elif args.command == "locust":
        locust_menu(python_path)
    else:
        main_menu(python_path)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        print_color("YELLOW", "Exiting...")
        sys.exit(130)
