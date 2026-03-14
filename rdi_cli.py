from rdi_vcs import RdiVcs

import argparse
import vcstool
import pygit2  # temp
import setuptools


print(argparse.__version__)
print(pygit2.__version__)
print(setuptools.__version__)


def main():
    rdi_vcs = RdiVcs('meta_repo/repos.yaml')
    # TODO: add meta-repo path as optional arg

    parser = argparse.ArgumentParser(
        description="rdi-vcs tool - manage multiple repositories"
    )
    subparsers = parser.add_subparsers(dest="command")

    clone_parser = subparsers.add_parser("clone")
    checkout_create_parser = subparsers.add_parser("checkout-create")
    checkout_create_parser.add_argument("branch")
    push_parser = subparsers.add_parser("push")
    pull_parser = subparsers.add_parser("pull")
    publish_parser = subparsers.add_parser("publish")

    args = parser.parse_args()

    match args.command:
        case "clone":
            rdi_vcs.execute_threads(rdi_vcs.clone)

        case "checkout-create":
            rdi_vcs.execute_threads(rdi_vcs.checkout_create, args.branch)

        case "push":
            rdi_vcs.execute_threads(rdi_vcs.push)

        case "pull":
            rdi_vcs.execute_threads(rdi_vcs.pull)

        case "publish":
            rdi_vcs.execute_threads(rdi_vcs.publish)


if __name__ == '__main__':
    main()

