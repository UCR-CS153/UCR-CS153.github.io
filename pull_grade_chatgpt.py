import requests
import io
import zipfile
import os

# Set the API endpoint and authentication token
api_url_base = 'https://api.github.com'
auth_token = os.environ.get('GITHUB_AUTH_TOKEN') # You will need to set this environment variable with your personal access token

# Set the number of repositories to fetch per page
per_page = 100

# Get a list of all repositories in the UCR-CS153 organization
org_name = 'UCR-CS153'
repo_url = f'{api_url_base}/orgs/{org_name}/repos?per_page={per_page}'
repos = []
page = 1
while True:
    response = requests.get(f'{repo_url}&page={page}', headers={'Authorization': f'token {auth_token}'})
    response_repos = response.json()
    if not response_repos:
        break
    repos.extend(response_repos)
    page += 1

# Filter the list of repositories to include only those whose names start with 'lab1'
repos = [repo['name'] for repo in repos if repo['name'].startswith('lab1')]

# Loop through each repository and fetch the logs for every workflow run
for repo in repos:
    workflow_url = f'{api_url_base}/repos/{org_name}/{repo}/actions/runs'
    response = requests.get(workflow_url, headers={'Authorization': f'token {auth_token}'})
    workflows = response.json()['workflow_runs']
    for workflow in workflows:
        workflow_id = workflow['id']
        log_url = f'{workflow_url}/{workflow_id}/logs'
        response = requests.get(log_url, headers={'Authorization': f'token {auth_token}'})
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            log_text = zip_file.read('Autograding/3_Run educationautograding@v1.txt').decode()
        print(f'Logs for workflow {workflow_id} in repo {repo}:\n{log_text}\n')
        score_line = [line for line in log_text.split('\n') if 'Your score: ' in line]
        if score_line:
            score_str = score_line[0].split('Your score: ')[-1].strip()
            try:
                score = float(score_str)
                print(f'Score for workflow {workflow_id} in repo {repo}: {score}\n')
            except ValueError:
                print(f'Could not parse score for workflow {workflow_id} in repo {repo}\n')
        else:
            print(f'No score found for workflow {workflow_id} in repo {repo}\n')
