import os
import sys
import subprocess
import json
import requests

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPOSITORY')

def get_repo_name():
    remote_url = subprocess.getoutput('git config --get remote.origin.url')
    if not remote_url:
        raise ValueError("Could not determine the repository name from the git configuration.")
    repo_name = remote_url.split('/')[-1].rstrip('.git')
    return repo_name

def get_owner():
    repo_name = get_repo_name()
    return repo_name.split('/')[0]
    return repo_name.split('/')[0]

def generate_commit_message():
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
    prompt = "Generate a commit message for the following changes:\n\n"
    changes = subprocess.getoutput('git diff --name-only main...$(git rev-parse --abbrev-ref HEAD)')
    data = {
        "model": "text-davinci-003",
        "prompt": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt + changes
            }
        ],
        "max_tokens": 150,
        "temperature": 0.5,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": ["\n"]
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    try:
        response = requests.post("https://api.openai.com/v1/engines/text-davinci-003/completions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            completion = response_data['choices'][0]['text']
            commit_message = completion.strip()
            return commit_message
        else:
            raise ValueError("No completion found in the response.")
        return commit_message.strip()
    except requests.exceptions.RequestException as e:
        response_text = e.response.text if e.response else "No response text available."
        print(f"Failed to generate commit message: {e}\nResponse: {response_text}")
        sys.exit(1)

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
        branch_name = subprocess.getoutput('git rev-parse --abbrev-ref HEAD')
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
