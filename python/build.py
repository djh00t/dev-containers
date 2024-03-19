#!/usr/bin/env python3
import os
import subprocess
import sys

def check_buildx_available():
    if subprocess.run(["docker", "buildx", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
        print("docker buildx not available. Install it before running this script.")
        sys.exit(1)

def increment_version(version):
    major, minor, patch = map(int, version.split('.'))
    return f"{major}.{minor}.{patch+1}"

def main():
    check_buildx_available()

    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()

    app_name = os.getenv('APP_NAME')
    if not app_name:
        print("APP_NAME environment variable is not set.")
        sys.exit(1)

    # Check if the builder already exists, if not create a new builder
    builder_name = f"{app_name}_builder"
    builder_check = subprocess.run(["docker", "buildx", "inspect", builder_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if builder_check.returncode != 0:
        subprocess.run(["docker", "buildx", "create", "--name", builder_name], check=True)
    subprocess.run(["docker", "buildx", "use", builder_name], check=True)

    # Start up the builder
    subprocess.run(["docker", "buildx", "inspect", "--bootstrap"], check=True)

    # Build and push the image for both amd64 and arm64 architectures
    with open('./VERSION', 'r') as file:
        version = file.read().strip()
    print(f"Building version {version}")
    result = subprocess.run([
        "docker", "buildx", "build", "--platform", "linux/amd64,linux/arm64",
        "--tag", f"{app_name}:{version}", "--tag", f"{app_name}:latest",
        "--push", "."
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print("Build succeeded, version number will be incremented.")
        new_version = increment_version(version)
        with open('./VERSION', 'w') as file:
            file.write(new_version)
        print(f"Version number incremented to {new_version}.")
    else:
        print("Build failed, version number will not be incremented.")
        sys.exit(1)

    # Remove the builder when done
    subprocess.run(["docker", "buildx", "rm", builder_name], check=True)

if __name__ == "__main__":
    main()
