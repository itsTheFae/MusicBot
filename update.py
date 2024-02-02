#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from typing import Any, List


def yes_or_no_input(question: str) -> bool:
    """
    Prompt the user for a yes or no response to given `question`
    As many times as it takes to get yes or no.
    """
    while True:
        ri = input(f"{question} (y/n): ")

        if ri.lower() in ["yes", "y"]:
            return True

        if ri.lower() in ["no", "n"]:
            return False


def run_or_raise_error(cmd: List[str], message: str, **kws: Any) -> None:
    """
    Wrapper for subprocess.check_call that avoids shell=True

    :raises: RuntimeError  with given `message` as exception text.
    """
    try:
        subprocess.check_call(cmd, **kws)
    except (  # pylint: disable=duplicate-code
        OSError,
        PermissionError,
        FileNotFoundError,
        subprocess.CalledProcessError,
    ) as e:
        raise RuntimeError(message) from e


def update_deps() -> None:
    """
    Tries to upgrade MusicBot dependencies using pip module.
    This will use the same exe/bin as is running this code without version checks.
    """
    print("Attempting to update dependencies...")

    run_or_raise_error(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-warn-script-location",
            "--user",
            "-U",
            "-r",
            "requirements.txt",
        ],
        "Could not update dependencies. You need to update manually. "
        f"Run:  {sys.executable} -m pip install -U -r requirements.txt",
    )


def finalize() -> None:
    """Attempt to fetch the bot version constant and print it."""
    try:
        from musicbot.constants import (  # pylint: disable=import-outside-toplevel
            VERSION,
        )

        print(f"The current MusicBot version is:  {VERSION}")
    except ImportError:
        print(
            "There was a problem fetching your current bot version. "
            "The installation may not have completed correctly."
        )

    print("Done!")


def main() -> None:
    """
    Runs several checks, starting with making sure there is a .git folder
    in the current working path.
    Attempt to detect a git executable and use it to run git pull.
    Later, we try to use pip module to upgrade dependency modules.
    """
    print("Starting...")

    # Make sure that we're in a Git repository
    if not os.path.isdir(".git"):
        raise EnvironmentError("This isn't a Git repository.")

    git_bin = shutil.which("git")
    if not git_bin:
        raise EnvironmentError(
            "Could not locate `git` executable.  Auto-update may not be possible."
        )

    # Make sure that we can actually use Git on the command line
    # because some people install Git Bash without allowing access to Windows CMD
    run_or_raise_error(
        [git_bin, "--version"],
        "Couldn't use Git on the CLI. You will need to run 'git pull' yourself.",
        stdout=subprocess.DEVNULL,
    )

    print("Passed Git checks...")

    # Check that the current working directory is clean
    sp = subprocess.check_output(
        [git_bin, "status", "--porcelain"], universal_newlines=True
    )
    if sp:
        oshit = yes_or_no_input(
            "You have modified files that are tracked by Git (e.g the bot's source files).\n"
            "Should we try resetting the repo? You will lose local modifications."
        )
        if oshit:
            run_or_raise_error(
                [git_bin, "reset", "--hard"],
                "Could not reset the directory to a clean state.",
            )
        else:
            wowee = yes_or_no_input(
                "OK, skipping bot update. Do you still want to update dependencies?"
            )
            if wowee:
                update_deps()
            else:
                finalize()
            return

    print("Checking if we need to update the bot...")

    run_or_raise_error(
        [git_bin, "pull"],
        "Could not update the bot. You will need to run 'git pull' yourself.",
    )

    update_deps()
    finalize()


if __name__ == "__main__":
    main()
