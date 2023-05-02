from typing import List
from github import Github, WorkflowRun
import os
from urllib.request import urlopen
from zipfile import ZipFile
import re
from io import BytesIO

gh = Github(os.environ.get("GITHUB_TOKEN"))

user = gh.get_organization('UCR-CS153')


def repo_filer(prefix="lab1") -> List:
    _LIMIT = 0
    for repo in user.get_repos():
        if repo.name.startswith(prefix):
            yield repo
            _LIMIT -= 1
            if _LIMIT == 0:
                break

for i in repo_filer():
    netid = i.name.replace("lab1-system-call-", "") + ','
    try:
        wf:WorkflowRun.WorkflowRun = list(i.get_workflow_runs())[0]
        log_url = wf._requester.requestJson("GET", wf.logs_url)[1]['location']
        log = urlopen(log_url)
        log_zip = ZipFile(BytesIO(log.read() ))
        log_content = log_zip.open("Autograding/3_Run educationautograding@v1.txt").read().decode()
        # print(log_content)
        score = re.findall("Your score: (\d+) / 80", log_content)
        if score:
            print( netid + score[0] + f",{wf.created_at}")
    except:
        print(netid + "0")
