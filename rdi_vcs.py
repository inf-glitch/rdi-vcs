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
from threading import Thread
import subprocess
import os


class RdiVcs:

    class TokenCallbacks(RemoteCallbacks):

        def __init__(self, token: str):
            self._token = token

        def credentials(self, url, username, allowed_types):
            # GitHub accepts x-access-token as the username for HTTPS token auth.
            return pygit2.UserPass("x-access-token", self._token)

    def _is_ssh_github_url(self, url: str) -> bool:
        return url.startswith("git@github.com:")

    def _is_https_github_url(self, url: str) -> bool:
        return url.startswith("https://github.com/")

    def _get_token_callbacks(self):
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            return None
        return self.TokenCallbacks(token)
            
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
        
        try:
            with open(repos_config, 'r') as f:
                self.repos_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f'Config file not found: {repos_config}\n'
                'Tip: pass a config path via --config'
            )

    def clone(self, repo):
        name = repo['name']    
        url = repo['url']

        if self._is_ssh_github_url(url):
            print(
                f'{name} uses SSH URL ({url}). SSH auth is not supported.\n'
                'Please change the repo URL to HTTPS (https://github.com/owner/repo.git).'
            )
            return

        clone_path = os.path.abspath(f'{name}')
        if os.path.exists(clone_path):
            print(f'{clone_path} already exists, omitting directory')
            return

        print(f'Cloning {name} from {url} to {clone_path}...')
        json flat = j.flatten();

        try:
            callbacks = self._get_token_callbacks()
            if callbacks:
                clone_repository(url, clone_path, callbacks=callbacks)
            else:
                clone_repository(url, clone_path)
            print(f'Done cloning {name}')
        except Exception as e:
            print(f'Error cloning {name}: {e}')

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
            if self._is_ssh_github_url(remote.url):
                print(
                    f'{name} origin remote uses SSH URL ({remote.url}). SSH auth is not supported.\n'
                    'Please change the remote URL to HTTPS (https://github.com/owner/repo.git).'
                )
                return

            callbacks = self._get_token_callbacks()
            if callbacks:
                remote.fetch(callbacks=callbacks)
            else:
                remote.fetch()
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
            repo_obj = pygit2.Repository(repo_path)
            remote = repo_obj.remotes['origin']
            remote_url = remote.url

            token = os.environ.get('GITHUB_TOKEN')
            if not token:
                print(
                    'GITHUB_TOKEN environment variable not set.\n'
                    'Create a token at: https://github.com/settings/tokens\n'
                    'And set it to current shell session: export GITHUB_TOKEN=*your_token*\n'
                    'Or execute: echo export GITHUB_TOKEN=*your_token* >> ~/.zshrc\n'
                    'to add it to your shell configuration\n'
                    '====================================================================='
                )

            use_token = token and remote_url.startswith('https://')

            cmd = ['git', 'push', '-u', 'origin', 'HEAD']

            if use_token:
                url_parts = remote_url.split('://', 1)
                authed_url = f'{url_parts[0]}://{token}@{url_parts[1]}'
                cmd = ['git', 'push', authed_url]
                print(f'Using token auth for {name}')

            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f'Pushed {name} successfully')
                if result.stdout:
                    print(result.stdout)
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

    def pull(self, repo):
        name = repo['name']
        repo_path = os.path.abspath(name)
        if not os.path.exists(repo_path):
            print(f'Repository {name} not found at {repo_path}. Cannot pull.')
            return

        try:
            repo_obj = pygit2.Repository(repo_path)
            remote = repo_obj.remotes['origin']
            remote_url = remote.url

            token = os.environ.get('GITHUB_TOKEN')
            if not token:
                print(
                    'GITHUB_TOKEN environment variable not set.\n'
                    'Create a token at: https://github.com/settings/tokens\n'
                    'And set it to current shell session: export GITHUB_TOKEN=*your_token*\n'
                    'Or execute: echo export GITHUB_TOKEN=*your_token* >> ~/.zshrc\n'
                    'to add it to your shell configuration\n'
                    '====================================================================='
                )

            use_token = token and remote_url.startswith('https://')

            cmd = ['git', 'pull']

            if use_token:
                url_parts = remote_url.split('://', 1)
                authed_url = f'{url_parts[0]}://{token}@{url_parts[1]}'
                cmd = ['git', 'pull', authed_url]
                print(f'Using token auth for {name}')

            result = subprocess.run(
                cmd,
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

        except subprocess.TimeoutExpired:
            print(f'Pull timed out for {name}')

        except Exception as e:
            print(f'Error pulling {name}: {e}')

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
                return
            elif r.status_code == 422:
                error_msg = r.json().get('message', '')
                if 'pull request already exists' in error_msg:
                    print(f'Pull request already exists for {name} from branch "{current_branch}"')
                    return
            else:
                print(f'Failed to create MR for {name}: {r.status_code} - {r.text}')
                return

            print(f'Nothing to merge for {name} on {current_branch}')

        except Exception as e:
            print(f'Error publishing {name}: {e}')

    def commit(self, repo, message):
        name = repo['name']
        repo_path = os.path.abspath(name)
        if not os.path.exists(repo_path):
            print(f'Repository {name} not found at {repo_path}. Cannot commit.')
            return

        try:
            add_result = subprocess.run(
                ['git', 'add', '-A'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if add_result.returncode != 0:
                print(f'Failed to stage changes for {name} (exit code {add_result.returncode})')
                if add_result.stderr:
                    print(add_result.stderr)
                elif add_result.stdout:
                    print(add_result.stdout)
                return

            commit_result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if commit_result.returncode == 0:
                print(f'Committed {name} successfully')
                if commit_result.stdout:
                    print(commit_result.stdout)
                return

            combined_output = f'{commit_result.stdout}\n{commit_result.stderr}'.lower()
            if 'nothing to commit' in combined_output or 'no changes added to commit' in combined_output:
                print(f'No changes to commit for {name}')
                return

            print(f'Commit failed for {name} (exit code {commit_result.returncode})')
            if commit_result.stderr:
                print(commit_result.stderr)
            elif commit_result.stdout:
                print(commit_result.stdout)

        except subprocess.TimeoutExpired:
            print(f'Commit timed out for {name}')
        except Exception as e:
            print(f'Error committing {name}: {e}')

    def execute_threads(self, *args):
        target = args[0]
        threads = []

        if len(args) == 2:
            extra_arg = args[1]  # <branch> / <message>
            for repo in self.repos_data['repos']:
                thread = Thread(target=target, args=(repo, extra_arg))
                thread.start()
                threads.append(thread)

        elif len(args) == 1:
            for repo in self.repos_data['repos']:
                thread = Thread(target=target, args=(repo,))
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()

    # def _vcs_command_exists(self):
    #     from shutil import which
    #     return which('vcs') is not None
