#!/usr/bin/env python3
import os
import json
import subprocess
import sys
from dotenv import load_dotenv

def check_buildx_available():
    if subprocess.run(["docker", "buildx", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
        print("docker buildx not available. Install it before running this script.")
        sys.exit(1)

def increment_version(version):
    major, minor, patch = map(int, version.split('.'))
    return f"{major}.{minor}.{patch+1}"

def main():
    check_buildx_available()

    # Increment the version at the start
    with open('./VERSION', 'r') as file:
        current_version = file.read().strip()
    new_version = increment_version(current_version)
    with open('./VERSION', 'w') as file:
        file.write(new_version)
    print(f"Version number incremented to {new_version}.")

    # Load environment variables from .env file
    load_dotenv()

    # Load Docker configuration from ~/.docker/config.json
    docker_config_path = os.path.expanduser('~/.docker/config.json')
    if not os.path.exists(docker_config_path):
        print("Docker config not found at ~/.docker/config.json. Make sure Docker is configured correctly.")
        sys.exit(1)
    with open(docker_config_path, 'r') as config_file:
        docker_config = json.load(config_file)

    app_name = os.getenv('APP_NAME')
    repo = os.getenv('DOCKER_REPO')
    if not app_name or not repo:
        print("APP_NAME and DOCKER_REPO environment variables must be set.")
        sys.exit(1)

    # Check if the builder already exists, if not create a new builder
    builder_check = subprocess.run(["docker", "buildx", "inspect", app_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if builder_check.returncode != 0:
        subprocess.run(["docker", "buildx", "create", "--name", app_name], check=True)
    subprocess.run(["docker", "buildx", "use", app_name], check=True)

    # Start up the builder
    subprocess.run(["docker", "buildx", "inspect", "--bootstrap"], check=True)

    # Build and push the image for both amd64 and arm64 architectures
    print(f"Building version {new_version}")
    # Log in to Docker registry
    auths = docker_config.get('auths', {})
    registry_auth = auths.get(repo)
    if registry_auth:
        docker_username = registry_auth.get('username')
        docker_password = registry_auth.get('password')
        if docker_username and docker_password:
            login_result = subprocess.run([
                "docker", "login",
                "--username", docker_username, "--password-stdin",
                f"{repo}/{app_name}"
            ], input=docker_password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if login_result.returncode != 0:
                print("Docker login failed. Check your credentials.")
                sys.exit(1)
        else:
            print("Docker registry login credentials are not set in config.json.")
            sys.exit(1)

    result = subprocess.run([
        "docker", "buildx", "build", "--platform", "linux/amd64,linux/arm64",
        "--tag", f"{repo}/{app_name}:{version}", "--tag", f"{repo}/{app_name}:latest",
        "--tag", f"{repo}/{app_name}:{new_version}", "--tag", f"{repo}/{app_name}:latest",
        "--push", "."
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print("Build succeeded.")
    else:
        print("Build failed, version number will not be incremented.")
        sys.exit(1)

    # Remove the builder when done
    # subprocess.run(["docker", "buildx", "rm", app_name], check=True)

if __name__ == "__main__":
    main()
