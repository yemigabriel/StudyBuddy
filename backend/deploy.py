import argparse
import os
import shutil
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import boto3

ROOT = Path(__file__).parent.resolve()
BUILD_DIR = ROOT / "build" / "lambda"
DIST_DIR = ROOT / "dist"
ZIP_PATH = DIST_DIR / "studybuddy-backend.zip"


def run(command: list[str]) -> None:
    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", str(ROOT / ".uv-cache"))
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def package_lambda() -> Path:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    run(
        [
            "uv",
            "pip",
            "install",
            "--target",
            str(BUILD_DIR),
            "-r",
            "requirements.txt",
        ]
    )

    shutil.copy2(ROOT / "server.py", BUILD_DIR / "server.py")
    shutil.copytree(ROOT / "app", BUILD_DIR / "app")

    with ZipFile(ZIP_PATH, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in BUILD_DIR.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(BUILD_DIR))

    return ZIP_PATH


def upload_lambda(zip_path: Path, function_name: str) -> None:
    client = boto3.client("lambda")
    client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_path.read_bytes(),
        Publish=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Package and deploy StudyBuddy backend.")
    parser.add_argument(
        "--function-name",
        help="Lambda function name. If omitted, the script only packages the zip.",
    )
    args = parser.parse_args()

    zip_path = package_lambda()
    print(f"Created package: {zip_path}")

    if args.function_name:
        upload_lambda(zip_path, args.function_name)
        print(f"Uploaded package to Lambda function: {args.function_name}")


if __name__ == "__main__":
    main()
