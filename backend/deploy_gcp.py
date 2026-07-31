import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DOCKERFILE_PATH = ROOT / "Dockerfile"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def build_image(image_uri: str) -> None:
    print(f"Building Cloud Run image: {image_uri}")
    run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/amd64",
            "-f",
            str(DOCKERFILE_PATH),
            "-t",
            image_uri,
            ".",
        ]
    )


def push_image(image_uri: str) -> None:
    registry = image_uri.split("/")[0]
    print(f"Configuring Docker auth for Artifact Registry: {registry}")
    run(["gcloud", "auth", "configure-docker", registry, "--quiet"])
    print(f"Building and pushing Cloud Run image: {image_uri}")
    run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/amd64",
            "-f",
            str(DOCKERFILE_PATH),
            "-t",
            image_uri,
            "--push",
            ".",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and push StudyBuddy Cloud Run image.")
    parser.add_argument(
        "--image-uri",
        required=True,
        help="Full Artifact Registry image URI including tag.",
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Build the image locally without pushing it to Artifact Registry.",
    )
    args = parser.parse_args()

    if args.skip_push:
        build_image(args.image_uri)
        return

    push_image(args.image_uri)


if __name__ == "__main__":
    main()
