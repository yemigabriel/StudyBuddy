import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DOCKERFILE_PATH = ROOT / "Dockerfile.lambda"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def build_image(image_uri: str) -> None:
    print(f"Building Lambda container image: {image_uri}")
    run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/amd64",
            "--provenance=false",
            "--sbom=false",
            "-f",
            str(DOCKERFILE_PATH),
            "-t",
            image_uri,
            ".",
        ]
    )


def login_to_ecr(registry: str) -> None:
    print(f"Logging in to ECR registry: {registry}")
    password = subprocess.check_output(
        ["aws", "ecr", "get-login-password"],
        text=True,
    )
    subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin", registry],
        input=password,
        text=True,
        check=True,
    )


def push_image(image_uri: str) -> None:
    registry = image_uri.split("/")[0]
    login_to_ecr(registry)
    print(f"Building and pushing Lambda container image: {image_uri}")
    run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/amd64",
            "--provenance=false",
            "--sbom=false",
            "-f",
            str(DOCKERFILE_PATH),
            "-t",
            image_uri,
            "--push",
            ".",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and push StudyBuddy Lambda image.")
    parser.add_argument(
        "--ecr-uri",
        required=True,
        help="Full ECR image URI including tag.",
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Build the image locally without pushing it to ECR.",
    )
    args = parser.parse_args()

    if not args.skip_push:
        push_image(args.ecr_uri)
    else:
        build_image(args.ecr_uri)


if __name__ == "__main__":
    main()
