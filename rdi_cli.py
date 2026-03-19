from rdi_vcs import RdiVcs

import argparse
import vcstool
import pygit2  # temp
import setuptools
import os
from pathlib import Path


def _persist_config_location(path: str) -> None:
    env_path = Path.home() / ".env.sh"
    export_line = f'export RDI_VCS_CONFIG_LOCATION="{path}"'

    existing = ""
    if env_path.exists():
        existing = env_path.read_text(encoding="utf-8")

    lines = existing.splitlines()
    out_lines = []
    replaced = False
    for line in lines:
        if line.strip().startswith("export RDI_VCS_CONFIG_LOCATION="):
            out_lines.append(export_line)
            replaced = True
        else:
            out_lines.append(line)

    if not replaced:
        if out_lines and out_lines[-1].strip() != "":
            out_lines.append("")
        out_lines.append(export_line)

    env_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def _resolve_config_path(arg_value: str) -> str:
    if arg_value is not None:
        return arg_value
    env_value = os.environ.get("RDI_VCS_CONFIG_LOCATION")
    if env_value:
        return env_value
    raise SystemExit(
        "No config path provided.\n"
        "Either:\n"
        "  - run: rdi-vcs set-config /path/to/repos.yaml\n"
        "  - or pass --config /path/to/repos.yaml explicitly\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="rdi-vcs tool - manage multiple repositories"
    )
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help="Path to repos YAML config (overrides RDI_VCS_CONFIG_LOCATION)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print dependency versions and extra debug output",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    set_config_parser = subparsers.add_parser("set-config")
    set_config_parser.add_argument("path", help="Config path to persist")

    clone_parser = subparsers.add_parser("clone")
    checkout_create_parser = subparsers.add_parser("checkout-create")
    checkout_create_parser.add_argument("branch")
    push_parser = subparsers.add_parser("push")
    pull_parser = subparsers.add_parser("pull")
    publish_parser = subparsers.add_parser("publish")

    args = parser.parse_args()

    if args.debug:
        print(argparse.__version__)
        print(pygit2.__version__)
        print(setuptools.__version__)


    if args.command == "set-config":
        _persist_config_location(args.path)
        print(f'Persisted RDI_VCS_CONFIG_LOCATION to: {args.path}')
        return

    config_path = _resolve_config_path(args.config)
    rdi_vcs = RdiVcs(config_path)

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

