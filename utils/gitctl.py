#!/usr/bin/env python3
#TODO implement `git ls-remote --size <repository_url>` before doing anything! )

# USE IT AT YOUR OWN RISK. Work on error handling in progress.

import os
import subprocess
import sys
import requests
from urllib.parse import urlparse

BASE_DIR = os.path.expanduser("~/data/src")

def get_repo_path(url):
    parsed_url = urlparse(url)
    if not parsed_url.netloc:
        print(f"Error: Invalid URL {url}")
        return None

    site = parsed_url.netloc
    user = None
    project = None

    if site == "github.com":
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) >= 2:
            user = path_parts[0]
            project = path_parts[1].replace(".git", "")
    else:
        print(f"Error: Unsupported site: {site}")
        return None

    if user and project:
        return os.path.join(BASE_DIR, site, user, project)
    else:
        print(f"Error: Invalid URL {url}")
        return None


def clone_repo(url):
    repo_path = get_repo_path(url)
    if not repo_path:
        return

    if os.path.exists(repo_path):
        response = input(f"Repository '{url}' already exists, do you want to update it? (y/n): ")
        if response.lower() != "y":
            return

        cmd = f"git -C '{repo_path}' pull"
    else:
        os.makedirs(repo_path, exist_ok=True)
        cmd = f"git clone '{url}' '{repo_path}'"

    print(f"Cloning into '{repo_path}'...")
    subprocess.run(cmd, shell=True)


def update_repos(directories="."):
    repos = []
    for directory in directories:
        for root, dirs, files in os.walk(directory):
            if ".git" in dirs:
                repo_path = os.path.join(root, ".git")
                if os.path.isdir(repo_path):
                    repos.append(os.path.dirname(repo_path))

    if not repos:
        print("No Git repositories found")
        return

    print("Found Git repositories:")
    for repo in repos:
        print(repo)

    response = input("Update the above Git repositories? [y/N] ")
    if response.lower() != "y":
        print("Aborting update")
        return

    for repo in repos:
        print(f"Updating {repo}...")
        subprocess.run(["git", "-C", repo, "pull"], check=True)
    print("All Git repositories updated successfully")


def main():
    if len(sys.argv) < 2:
        print("Error: Missing URL or directory argument")
        print("Usage: {} [url or directory] [directory2] ...".format(sys.argv[0]))
        sys.exit(1)

    # Check if arguments are URLs or directories
    urls = []
    directories = []
    for arg in sys.argv[1:]:
        if arg.startswith("http") or arg.startswith("git") or arg.startswith("ssh"):
            urls.append(arg)
        else:
            directories.append(arg)

    # Clone or pull repos from URLs
    for url in urls:
        try:
            r = requests.get(url)
            if r.status_code == 404:
                print(f"Error: Repository '{url}' not found")
                continue
            clone_repo(url)
        except requests.exceptions.RequestException:
            print(f"Error: Failed to access '{url}'")

    # Update repos in directories
    update_repos(directories)


if __name__ == "__main__":
    main()
