# repos structure:
#   repos:
#       - name:
#         type:
#         url:
#         version:
#       - name:
#         ...


import pygit2
import requests
from pygit2 import clone_repository, RemoteCallbacks
import yaml
from getpass import getuser
from threading import Thread
import subprocess
import os


class RdiVcs:

    class SshKeyCallbacks(RemoteCallbacks):

        def credentials(self, url, username, allowed_types):
            return pygit2.Keypair(
                username,
                '/home/' + getuser() + '/.ssh/git.pub',
                '/home/' + getuser() + '/.ssh/git',
                ''
            )
            
    def _get_github_repo_info(self, url):
        # parsing a name also as overhead to handle
        # difference in local dir name if present

        if url.startswith('git@github.com:'):
            path = url[15:]
        elif url.startswith('https://github.com/'):
            path = url[19:]
        else:
            raise ValueError(f'Unsupported URL format: {url}')

        if path.endswith('.git'):
            path = path[:-4]
        parts = path.split('/')
        if len(parts) != 2:
            raise ValueError(f'Invalid GH repo path: {path}')
        return parts[0], parts[1]

    def __init__(self, repos_config):
        print('got config:', repos_config, '\n')
        
        with open(repos_config, 'r') as f:
            self.repos_data = yaml.safe_load(f)
    def clone(self, repo):
        name = repo['name']    
        url = repo['url']

        clone_path = os.path.abspath(f'{name}')
        if os.path.exists(clone_path):
            print(f'{clone_path} already exists, omitting directory')
            return

        print(f'Cloning {name} from {url} to {clone_path}...')

        try:
            clone_repository(url, clone_path, callbacks=self.SshKeyCallbacks())
            print(f'Done cloning {name}')
        except Exception as e:
            print(f'Error cloning {name}: {e}')

    # TODO: unify the _all_ method for all commands
    def clone_all(self):
        threads = []

        for repo in self.repos_data['repos']:
            thread = Thread(target=self.clone, args=(repo,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def checkout_create(self, repo, branch):
        name = repo['name']
        repo_path = os.path.abspath(name)
        if not os.path.exists(repo_path):
            print(f'Repository {name} not found at {repo_path}. Clone it first.')
            return

        try:
            repo_obj = pygit2.Repository(repo_path)
        except Exception as e:
            print(f'Error opening repo {name}: {e}')
            return
        try:
            remote = repo_obj.remotes['origin']
            callbacks = self.SshKeyCallbacks()
            remote.fetch(callbacks=callbacks)
        except Exception as e:
            print(f'Fetch failed for {name}: {e}')

        # check if local branch exists
        local_branch = repo_obj.branches.get(branch)
        if local_branch:
            print(f'Branch "{branch}" exists locally in {name}. Checking out.')
            repo_obj.checkout(local_branch.name)
            print(f'{name} is now at {branch}')
            return

        # check if remote branch exists
        remote_branch_name = f'origin/{branch}'
        remote_branch = repo_obj.branches.get(remote_branch_name)
        if remote_branch:
            print(f'Remote branch "{remote_branch_name}" found for repo: {name}')
            commit = repo_obj[remote_branch.target]
            new_branch = repo_obj.branches.create(branch, commit)
            new_branch.upstream = remote_branch
            repo_obj.checkout(new_branch.name)
            print(f'{name} is now at {branch}')
            return

        # if both absent
        print(f'Branch "{branch}" does not exist neither remotely nor locally')
        head_commit = repo_obj.head.peel(pygit2.Commit)
        new_branch = repo_obj.branches.create(branch, head_commit)
        repo_obj.checkout(new_branch.name)
        print(f'{name} is now at {branch}')

    def checkout_create_all(self, branch):
        threads = []

        for repo in self.repos_data['repos']:
            thread = Thread(target=self.checkout_create, args=(repo, branch))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def push(self, repo):
        name = repo['name']
        vcs_type = repo['type'] 
        repo_path = os.path.abspath(name)
        if not os.path.exists(repo_path):
            print(f'Repository {name} not found at {repo_path}. Cannot push.')
            return

        # if not self._vcs_command_exists():
        #     print('"vcs" command not found. Is vcs tool installed in PATH?')
        #     return

        try:
            result = subprocess.run(
                ['git', 'push', '-u', 'origin', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f'Pushed {name} successfully')
            else:
                print(f'Push failed for {name} (exit code {result.returncode})')
                if result.stderr:
                    print(result.stderr)
                elif result.stdout:
                    print(result.stdout)

        except subprocess.TimeoutExpired:
            print(f'Push timed out for {name}')

        except Exception as e:
            print(f'Error pushing {name}: {e}')

    def push_all(self):
        threads = []
        for repo in self.repos_data['repos']:
            thread = Thread(target=self.push, args=(repo,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def pull(self, repo):
        name = repo['name']
        repo_path = os.path.abspath(name)
        if not os.path.exists(repo_path):
            print(f'Repository {name} not found at {repo_path}. Cannot pull.')
            return

        try:
            result = subprocess.run(
                ['git', 'pull'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f'Pulled {name} successfully')
                if result.stdout:
                    print(result.stdout)
            else:
                print(f'Pull failed for {name} (exit code {result.returncode})')
                if result.stderr:
                    print(result.stderr)
                elif result.stdout:
                    print(result.stdout)

        except subprocess.TimoutExpired:
            print(f'Pull timed out for {name}')

        except Exception as e:
            print(f'Error pulling {name}: {e}')

    def pull_all(self):
        threads = []
        for repo in self.repos_data['repos']:
            thread = Thread(target=self.pull, args=(repo,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def publish(self, repo):
        name = repo['name']
        repo_path = os.path.abspath(name)
        if not os.path.exists(repo_path):
            print(f'Repository {name} not found at {repo_path}. Cannot publish.')
            return

        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            print(
                'GITHUB_TOKEN environment variable not set.\n'
                f'MR for {name} could not be created.\n'
                'Create a token at: https://github.com/settings/tokens\n'
                'And set it to current shell session: export GITHUB_TOKEN=*your_token*\n'
                'Or execute: echo export GITHUB_TOKEN=*your_token* >> ~/.zshrc\n'
                'to add it to your shell configuration\n'
                '====================================================================='
            )
            return

        try:
            repo_obj = pygit2.Repository(repo_path)
            current_branch = repo_obj.head.shorthand
            print(f'Current branch is "{current_branch}"')

            remote = repo_obj.remotes['origin']
            remote_url = remote.url
            owner, repo_name = self._get_github_repo_info(remote_url)

            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            repo_info_url = f'https://api.github.com/repos/{owner}/{repo_name}'
            r = requests.get(repo_info_url, headers=headers)
            
            if r.status_code != 200:
                print(f'Failed to get repository info for {name}: {r.status_code} - \
                        {r.text}')

            default_branch = r.json()['default_branch']

            mr_url = f'https://api.github.com/repos/{owner}/{repo_name}/pulls'
            payload = {
                'title': f'Merge request from {current_branch}',
                'head': current_branch,
                'base': default_branch
            }
            r = requests.post(mr_url, json=payload, headers=headers)

            if r.status_code == 201:
                mr_data = r.json()
                html_url = mr_data['html_url']
                print(f'Repository: {name} -> {html_url}')
            elif r.status_code == 422:
                error_msg = r.json().get('message', '')
                if 'pull request already exists' in error_msg:
                    print(f'Pull request already exists for {name} from branch u"{current_branch}"')
            else:
                print(f'Failed to create MR for {name}: {r.status_code} - {r.text}')

        except Exception as e:
            print(f'Error publishing {name}: {e}')

    def publish_all(self):
        threads = []

        for repo in self.repos_data['repos']:
            thread = Thread(target=self.publish, args=(repo,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    # def _vcs_command_exists(self):
    #     from shutil import which
    #     return which('vcs') is not None
