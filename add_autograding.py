import os
import json
import sys

def create_folder_structure(base_path=".github"):
    # Create .github, workflows, and classroom directories
    workflows_path = os.path.join(base_path, "workflows")
    classroom_path = os.path.join(base_path, "classroom")
    print(f"Creating {workflows_path}")
    os.makedirs(workflows_path, exist_ok=True)
    print(f"Creating {classroom_path}")
    os.makedirs(classroom_path, exist_ok=True)
    return workflows_path, classroom_path

def create_autograding_json(lab_name, classroom_path):
    autograding_content = {
        "tests": [
            {
                "name": f"{lab_name} auto grader",
                "setup": f"sudo apt-get update >/dev/null 2>&1 && sudo apt-get install -y qemu-system-i386 >/dev/null 2>&1 && pip3 install pwntools >/dev/null 2>&1 && wget https://ucr-cs153.github.io/{lab_name}.py >/dev/null 2>&1",
                "run": f"python3 {lab_name}.py",
                "input": "",
                "output": "",
                "comparison": "exact",
                "timeout": 10,
                "points": None
            }
        ]
    }
    with open(os.path.join(classroom_path, "autograding.json"), "w") as f:
        json.dump(autograding_content, f, indent=2)

def create_classroom_yml(workflows_path):
    classroom_yml_content = """name: GitHub Classroom Workflow

on:
  push:
  workflow_dispatch:

permissions:
  checks: write
  actions: read
  contents: read

jobs:
  build:
    name: Autograding
    runs-on: ubuntu-latest
    if: github.actor != 'github-classroom[bot]'
    steps:
      - uses: actions/checkout@v4
      - uses: education/autograding@v1
"""
    with open(os.path.join(workflows_path, "classroom.yml"), "w") as f:
        f.write(classroom_yml_content)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <lab_name>. <lab_name> should be lab1, lab2, lab3 or lab4")
        sys.exit(1)
    lab_name = sys.argv[1]
    if lab_name not in ["lab1", "lab2", "lab3", "lab4"]:
        print("Usage: python script.py <lab_name>. <lab_name> should be lab1, lab2, lab3 or lab4")
        sys.exit(1)
    workflows_path, classroom_path = create_folder_structure()
    create_autograding_json(lab_name, classroom_path)
    create_classroom_yml(workflows_path)
    print(f"Setup completed for {lab_name}.")

if __name__ == "__main__":
    main()
