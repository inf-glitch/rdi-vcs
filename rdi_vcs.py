# repos structure:
#   repos:
#       - name:
#         type:
#         url:
#         version:
#       - name:
#         ...


from threading import Thread
import pygit2
from pygit2 import clone_repository, RemoteCallbacks
import yaml
from getpass import getuser
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

    def __init__(self, repos_config):
        print('got config:', repos_config)
        
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
            new_branch = repo_obj.braches.create(branch, commit)
            new_branch.upstream = remote_branch_name
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


    def pull(self):
        print('pull command plug')
        return

    def push(self):
        print('push command plug')
        return

    def publish(self):
        print('publish command plug')
        return
