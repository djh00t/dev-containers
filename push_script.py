import os
import subprocess
import json
import requests

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPOSITORY')

if REPO_NAME is None:
    raise ValueError("GITHUB_REPOSITORY environment variable is not set.")
else:
    OWNER = REPO_NAME.split('/')[0]

def generate_commit_message():
    prompt = "Generate a commit message for the following changes:\n\n"
    changes = subprocess.getoutput('git diff --name-only main...$(git rev-parse --abbrev-ref HEAD)')
    data = {
        "model": "text-davinci-003",
        "prompt": prompt + changes,
        "temperature": 0.5,
        "max_tokens": 150
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    response = requests.post("https://api.openai.com/v1/engines/davinci/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['text'].strip()

def create_or_update_pull_request(commit_message):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    pr_title = commit_message.split('\n')[0]
    changelog = generate_changelog()
    pr_body = f"## Changelog\n{changelog}\n\n## Commit Message\n{commit_message}\n\n---\n*This PR was generated using OpenAI's ChatGPT-3.5 Turbo.*"
    data = {
        "title": pr_title,
        "body": pr_body,
        "head": branch_name,
        "base": "main"
    }
    response = requests.post(f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/pulls", headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def generate_changelog():
    changelog = subprocess.getoutput('git log main..HEAD --oneline')
    if not changelog:
        return "No new changes to report."
    return changelog

def main():
    current_branch = subprocess.getoutput('git rev-parse --abbrev-ref HEAD')
    if current_branch == 'main':
        branch_name = os.getenv('BRANCH_NAME')
        subprocess.run(['git', 'checkout', '-b', branch_name])
        subprocess.run(['git', 'tag', '-a', branch_name, '-m', f"Release {branch_name}"])
        subprocess.run(['git', 'push', 'origin', branch_name, '--tags'])
    else:
        if os.getenv('LOG_LEVEL') == 'DEBUG':
            print("Debug logging is enabled. Displaying diffs...")
            git_diffs = subprocess.getoutput(f'git diff --name-only main...{current_branch} | xargs -I {{}} git diff main...{current_branch} -- {{}}')
            print(git_diffs)
        commit_message = generate_commit_message()
        subprocess.run(['git', 'commit', '-am', commit_message])
        subprocess.run(['git', 'push', 'origin', current_branch])
        create_or_update_pull_request(commit_message)

        # Additional logic for generating commit message and pull request notes
        # ...

if __name__ == '__main__':
    main()
