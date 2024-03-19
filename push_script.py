import os
import re
import sys
import subprocess
import json
import requests
from urllib.parse import urlparse

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def get_git_remote_info():
    remote_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode().strip()
    if not remote_url:
        raise ValueError("Could not determine the git remote URL from the git configuration.")
    match = re.match(r'^(?:https?://|git@)github\.com[/:](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$', remote_url)
    if match:
        return match.group('owner'), match.group('repo')
    raise ValueError("The git remote URL is not a valid GitHub repository URL.")

def generate_commit_message():
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
    prompt = "Generate a commit message for the following changes:\n\n"
    changes = subprocess.getoutput('git diff --name-only main...$(git rev-parse --abbrev-ref HEAD)')
    messages = [
            {
                "role": "system",
                "content": prompt + changes
            },
            {
                "role": "user",
                "content": "Please generate a commit message for the changes listed above."
            }
    ]
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json={
            "model": "gpt-3.5-turbo",
            "messages": messages
        })
        response.raise_for_status()
        response_data = response.json()
        if 'choices' in response_data and response_data['choices'] and 'message' in response_data['choices'][0]:
            commit_message = response_data['choices'][0]['message']['content'].strip()
            return commit_message
        else:
            raise ValueError("No completion found in the response.")
    except requests.exceptions.RequestException as e:
        response_text = e.response.text if e.response else "No response text available."
        print(f"Failed to generate commit message: {e}\nResponse: {response_text}")
        sys.exit(1)

def create_or_update_pull_request(commit_message, branch_name):
    OWNER, REPO_NAME = get_git_remote_info()
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    pr_title = commit_message.split('\n')[0]
    changelog = generate_changelog()
    pr_body = f"## Changelog\n{changelog}\n\n## Commit Message\n{commit_message}\n\n## Branch\n{branch_name}"
    # Check if a pull request already exists for the branch
    existing_pr_response = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/pulls?head={OWNER}:{branch_name}", headers=headers)
    existing_pr_response.raise_for_status()
    existing_prs = existing_pr_response.json()
    if existing_prs:
        # Update the existing pull request
        pr_number = existing_prs[0]['number']
        update_response = requests.patch(f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/pulls/{pr_number}", headers=headers, json={"title": pr_title, "body": pr_body})
        update_response.raise_for_status()
        return update_response.json()
    else:
        # Create a new pull request
        data = {
            "title": pr_title,
            "body": pr_body,
            "head": branch_name,
            "base": "main"
        }
        response = requests.post(f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/pulls", headers=headers, json=data)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            # Log the response body for debugging purposes
            print(f"GitHub API returned 422 Unprocessable Entity: {e.response.json()}")
        else:
            raise
    return response.json()

def generate_changelog():
    changelog_entries = subprocess.getoutput("git log --reverse --format='%ad %H %s (%an)' --date=short | sed -e 's/aider: //g'").split('\n')
    changelog_content = ""
    for entry in changelog_entries:
        date, commit_id, message, author = entry.split(' ', 3)
        changelog_content += f"- {date} - {message} - {commit_id} - {author}\n"
    with open('CHANGELOG.md', 'w') as changelog_file:
        changelog_file.write(changelog_content)
    return changelog_content

def main():
    current_branch = subprocess.getoutput('git rev-parse --abbrev-ref HEAD')
    if current_branch == 'main':
        branch_name = subprocess.getoutput('git symbolic-ref --short HEAD')
        branch_name = subprocess.getoutput('git rev-parse --abbrev-ref HEAD')
        subprocess.run(['git', 'tag', '-a', branch_name, '-m', f"Release {branch_name}"])
        subprocess.run(['git', 'push', 'origin', branch_name, '--tags'])
    else:
        if os.getenv('LOG_LEVEL') == 'DEBUG':
            print("Debug logging is enabled. Displaying diffs...")
            git_diffs = subprocess.getoutput(f'git diff --name-only main...{current_branch} | xargs -I {{}} git diff main...{current_branch} -- {{}}')
            print(git_diffs)
        commit_message = generate_commit_message()
        generate_changelog()
        subprocess.run(['git', 'commit', '-am', commit_message])
        subprocess.run(['git', 'push', 'origin', current_branch])
        owner, repo_name = get_git_remote_info()
        create_or_update_pull_request(commit_message, current_branch)

        # Additional logic for generating commit message and pull request notes
        # ...

if __name__ == '__main__':
    main()
