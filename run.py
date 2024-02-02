#!/usr/bin/env python3

import asyncio
import importlib.util
import logging
import os
import pathlib
import shutil
import ssl
import subprocess
import sys
import time
import traceback
from base64 import b64decode
from typing import Any, Union

from musicbot.constants import VERSION as BOTVERSION
from musicbot.exceptions import HelpfulError, RestartSignal, TerminateSignal
from musicbot.utils import rotate_log_files, setup_loggers, shutdown_loggers

# take care of loggers right away
log = logging.getLogger("musicbot.launcher")
setup_loggers()
log.info("Loading MusicBot version:  %s", BOTVERSION)
log.info("Log opened:  %s", time.ctime())


try:
    import aiohttp
except ImportError:
    pass


class GIT:
    @classmethod
    def works(cls) -> bool:
        """Checks for output from git --version to verify git can be run."""
        try:
            git_bin = shutil.which("git")
            if not git_bin:
                return False
            return bool(subprocess.check_output([git_bin, "--version"]))
        except (
            OSError,
            ValueError,
            PermissionError,
            FileNotFoundError,
            subprocess.CalledProcessError,
        ):
            return False

    @classmethod
    def run_upgrade_pull(cls) -> None:
        """Runs `git pull` in the current working directory."""
        if not cls.works():
            raise RuntimeError("Cannot locate or run 'git' executable.")

        log.info("Attempting to upgrade with `git pull` on current path.")
        try:
            git_bin = shutil.which("git")
            if not git_bin:
                raise FileNotFoundError("Could not locate `git` executable on path.")
            raw_data = subprocess.check_output([git_bin, "pull"])
            git_data = raw_data.decode("utf8").strip()
            log.info("Result of git pull:  %s", git_data)
        except (
            OSError,
            UnicodeError,
            PermissionError,
            FileNotFoundError,
            subprocess.CalledProcessError,
        ):
            log.exception("Upgrade failed, you need to run `git pull` manually.")


class PIP:
    @classmethod
    def run(cls, command: str, check_output: bool = False) -> Union[bytes, int]:
        """Runs a pip command using `sys.exectutable -m pip` through subprocess.
        Given `command` is split before it is passed, so quoted items will not work.
        """
        if not cls.works():
            raise RuntimeError("Cannot execute pip.")

        try:
            return cls.run_python_m(*command.split(), check_output=check_output)
        except subprocess.CalledProcessError as e:
            return e.returncode
        except (OSError, PermissionError, FileNotFoundError):
            log.exception("Error using -m method")
        return 0

    @classmethod
    def run_python_m(cls, *args: Any, **kwargs: Any) -> Union[bytes, int]:
        """
        Use subprocess check_call or check_output to run a pip module
        command using the `args` as additional arguments to pip.
        The returned value of the call is returned from this method.

        :param: check_output:  Use check_output rather than check_call.
        """
        check_output = kwargs.pop("check_output", False)
        if check_output:
            return subprocess.check_output([sys.executable, "-m", "pip"] + list(args))
        return subprocess.check_call([sys.executable, "-m", "pip"] + list(args))

    @classmethod
    def run_install(
        cls, cmd: str, quiet: bool = False, check_output: bool = False
    ) -> Union[bytes, int]:
        """
        Runs pip install command and returns the command exist status.

        :param: cmd:  a string of arguments passed to `pip install`.
        :param: quiet:  attempt to silence output using -q command flag.
        :param: check_output:  return command output instead of exit code.
        """
        q_flag = "-q " if quiet else ""
        return cls.run(f"install {q_flag}{cmd}", check_output)

    @classmethod
    def works(cls) -> bool:
        """Checks for output from pip --version to verify pip can be run."""
        try:
            return bool(cls.run_python_m(["--version"], check_output=True))
        except (
            OSError,
            PermissionError,
            FileNotFoundError,
            subprocess.CalledProcessError,
        ):
            return False

    @classmethod
    def run_upgrade_requirements(cls) -> None:
        """
        Uses a subprocess call to run python using sys.executable.
        Runs `pip install --upgrade -r ./requirements.txt`
        """
        if not cls.works():
            raise RuntimeError("Cannot locate or execute python -m pip")

        log.info(
            "Attempting to upgrade with `pip install --upgrade -r requirements.txt` on current path."
        )
        try:
            raw_data = cls.run_python_m(
                ["install", "--upgrade", "-r", "requirements.txt"],
                check_output=True,
            )
            if isinstance(raw_data, bytes):
                pip_data = raw_data.decode("utf8").strip()
                log.info("Result of pip upgrade:  %s", pip_data)
        except (
            OSError,
            UnicodeError,
            PermissionError,
            FileNotFoundError,
            subprocess.CalledProcessError,
        ):
            log.exception(
                "Upgrade failed, you need to run `pip install --upgrade -r requirements.txt` manually."
            )


def bugger_off(msg: str = "Press enter to continue . . .", code: int = 1) -> None:
    """Make the console wait for the user to press enter/return."""
    input(msg)
    sys.exit(code)


def sanity_checks(optional: bool = True) -> None:
    """
    Run a collection of pre-startup checks to either automatically correct
    issues or inform the user of how to correct them.
    """
    log.info("Starting sanity checks")
    """Required Checks"""
    # Make sure we're on Python 3.8+
    req_ensure_py3()

    # Make sure we're in a writable env
    req_ensure_env()

    # Make our folders if needed
    pathlib.Path("data").mkdir(exist_ok=True)

    # For rewrite only
    req_check_deps()

    log.info("Required checks passed.")

    """Optional Checks"""
    if not optional:
        return

    # Check disk usage
    opt_check_disk_space()

    log.info("Optional checks passed.")


def req_ensure_py3() -> None:
    """
    Verify the current running version of Python and attempt to find a
    suitable minimum version in the system if the running version is too old.
    """
    log.info("Checking for Python 3.8+")

    if sys.version_info < (3, 8):
        log.warning(
            "Python 3.8+ is required. This version is %s", sys.version.split()[0]
        )
        log.warning("Attempting to locate Python 3.8...")
        # Should we look for other versions than min-ver?

        pycom = None

        if sys.platform.startswith("win"):
            pycom = shutil.which("py.exe")
            if not pycom:
                log.warning("Could not locate py.exe")

            try:
                subprocess.check_output([pycom, "-3.8", '-c "exit()"'])
                pycom = f"{pycom} -3.8"
            except (
                OSError,
                PermissionError,
                FileNotFoundError,
                subprocess.CalledProcessError,
            ):
                log.warning("Could not execute `py.exe -3.8` ")
                pycom = None

            if pycom:
                log.info("Python 3 found.  Launching bot...")
                os.system(f"start cmd /k {pycom} run.py")
                sys.exit(0)

        else:
            log.info('Trying "python3.8"')
            pycom = shutil.which("python3.8")
            if not pycom:
                log.warning("Could not locate python3.8 on path.")

            try:
                subprocess.check_output([pycom, '-c "exit()"'])
            except (
                OSError,
                PermissionError,
                FileNotFoundError,
                subprocess.CalledProcessError,
            ):
                pycom = None

            if pycom:
                log.info(
                    "\nPython 3.8 found.  Re-launching bot using: %s run.py\n", pycom
                )
                os.execlp(pycom, pycom, "run.py")

        log.critical(
            "Could not find Python 3.8 or higher.  Please run the bot using Python 3.8"
        )
        bugger_off()


def req_check_deps() -> None:
    """
    Check that we have the required dependency modules at the right versions.
    """
    try:
        import discord  # pylint: disable=import-outside-toplevel

        if discord.version_info.major < 2:
            log.critical(
                "This version of MusicBot requires a newer version of discord.py. "
                "Your version is %s. Try running update.py.",
                discord.__version__,
            )
            bugger_off()
    except ImportError:
        # if we can't import discord.py, an error will be thrown later down the line anyway
        pass


def req_ensure_env() -> None:
    """
    Inspect the environment variables, validating and updating values where needed.
    """
    log.info("Ensuring we're in the right environment")

    if os.environ.get("APP_ENV") != "docker" and not os.path.isdir(
        b64decode("LmdpdA==").decode("utf-8")
    ):
        log.critical(
            b64decode(
                "Qm90IHdhc24ndCBpbnN0YWxsZWQgdXNpbmcgR2l0LiBSZWluc3RhbGwgdXNpbmcgaHR0cDovL2JpdC5seS9tdXNpY2JvdGRvY3Mu"
            ).decode("utf-8")
        )
        bugger_off()

    try:
        # TODO: change these perhaps.
        assert os.path.isdir("config"), 'folder "config" not found'
        assert os.path.isdir("musicbot"), 'folder "musicbot" not found'
        assert os.path.isfile(
            "musicbot/__init__.py"
        ), "musicbot folder is not a Python module"

        assert importlib.util.find_spec("musicbot"), "musicbot module is not importable"
    except AssertionError as e:
        log.critical("Failed environment check, %s", e)
        bugger_off()

    try:
        os.mkdir("musicbot-test-folder")
    except (
        OSError,
        FileExistsError,
        PermissionError,
        IsADirectoryError,
    ):
        log.critical("Current working directory does not seem to be writable")
        log.critical("Please move the bot to a folder that is writable")
        bugger_off()
    finally:
        shutil.rmtree("musicbot-test-folder", True)

    if sys.platform.startswith("win"):
        log.info("Adding local bins/ folder to path")
        os.environ["PATH"] += ";" + os.path.abspath("bin/")
        sys.path.append(os.path.abspath("bin/"))  # might as well


def opt_check_disk_space(warnlimit_mb: int = 200) -> None:
    """
    Performs and optional check of system disk storage space to warn the
    user if the bot might gobble that remaining space with downloads later.
    """
    if shutil.disk_usage(".").free < warnlimit_mb * 1024 * 2:
        log.warning(
            "Less than %sMB of free space remains on this device",
            warnlimit_mb,
        )


#################################################


def respawn_bot_process(pybin: str = "") -> None:
    """
    Use a platform dependent method to restart the bot process, without
    an external process/service manager.
    This uses either the given `pybin` executable path or sys.executable
    to run the bot using the arguments currently in sys.argv

    This function attempts to make sure all buffers are flushed and logging
    is shut down before restarting the new process.

    On Linux/Unix-style OS this will use sys.execlp to replace the process
    while keeping the existing PID.

    On Windows OS this will use subprocess.Popen to create a new console
    where the new bot is started, with a new PID, and exit this instance.
    """
    if not pybin:
        pybin = os.path.basename(sys.executable)
    exec_args = [pybin] + sys.argv

    shutdown_loggers()
    rotate_log_files()

    sys.stdout.flush()
    sys.stderr.flush()
    logging.shutdown()

    if os.name == "nt":
        # On Windows, this creates a new process window that dies when the script exits.
        # Seemed like the best way to avoid a pile of processes While keeping clean output in the shell.
        # There is seemingly no way to get the same effect as os.exec* on unix here in windows land.
        # The moment we end our existing instance, control is returned to the starting shell.
        with subprocess.Popen(
            exec_args,
            # creationflags is only available under windows, so mypy may complain here.
            creationflags=subprocess.CREATE_NEW_CONSOLE,  # type: ignore[attr-defined]
        ):
            log.debug("Opened new MusicBot instance.  This terminal can now be closed!")
        sys.exit(0)
    else:
        # On Unix/Linux/Mac this should immediately replace the current program.
        # No new PID, and the babies all get thrown out with the bath.  Kinda dangerous...
        # We need to make sure files and things are closed before we do this.
        os.execlp(exec_args[0], *exec_args)


async def main() -> Union[RestartSignal, TerminateSignal, None]:
    """All of the MusicBot starts here."""
    # TODO: *actual* CLI arg parsing

    if "--no-checks" not in sys.argv:
        sanity_checks()

    exit_signal: Union[RestartSignal, TerminateSignal, None] = None
    tried_requirementstxt = False
    use_certifi = False
    tryagain = True

    loops = 0
    max_wait_time = 60

    while tryagain:
        # Maybe I need to try to import stuff first, then actually import stuff
        # It'd save me a lot of pain with all that awful exception type checking

        m = None
        try:
            from musicbot import MusicBot  # pylint: disable=import-outside-toplevel

            m = MusicBot(use_certifi=use_certifi)
            # await m._doBotInit(use_certifi)
            await m.run()

        except (
            ssl.SSLCertVerificationError,
            aiohttp.client_exceptions.ClientConnectorCertificateError,
        ) as e:
            if isinstance(
                e, aiohttp.client_exceptions.ClientConnectorCertificateError
            ) and isinstance(e.__cause__, ssl.SSLCertVerificationError):
                e = e.__cause__
            else:
                log.critical(
                    "Certificate error is not a verification error, not trying certifi and exiting."
                )
                break

            # In case the local trust store does not have the cert locally, we can try certifi.
            # We don't want to patch working systems with a third-party trust chain outright.
            # These verify_code values come from OpenSSL:  https://www.openssl.org/docs/man1.0.2/man1/verify.html
            if e.verify_code == 20:  # X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY
                if use_certifi:
                    log.exception(
                        "Could not get Issuer Cert even with certifi.  Try: pip install --upgrade certifi "
                    )
                    break

                log.warning(
                    "Could not get Issuer Certificate from default trust store, trying certifi instead."
                )
                use_certifi = True
                continue

        except SyntaxError:
            log.exception("Syntax error (this is a bug, not your fault)")
            break

        except ImportError:
            # TODO: if error module is in pip or dpy requirements...

            if not tried_requirementstxt:
                tried_requirementstxt = True

                log.exception("Error starting bot")
                log.info("Attempting to install dependencies...")

                err = PIP.run_install("--upgrade -r requirements.txt")

                if err:  # TODO: add the specific error check back.
                    # The proper thing to do here is tell the user to fix their install, not help make it worse.
                    # Comprehensive return codes aren't really a feature of pip, we'd need to read the log, and so does the user.
                    print()
                    log.critical(
                        "This is not recommended! You can try to %s to install dependencies anyways.",
                        ["use sudo", "run as admin"][sys.platform.startswith("win")],
                    )
                    break

                print()
                log.info("Ok lets hope it worked")
                print()
            else:
                log.exception("Unknown ImportError, exiting.")
                break

        except HelpfulError as e:
            log.info(e.message)
            break

        except TerminateSignal as e:
            exit_signal = e
            break

        except RestartSignal as e:
            if e.get_name() == "RESTART_SOFT":
                loops = 0
            else:
                exit_signal = e
                break

        except Exception:  # pylint: disable=broad-exception-caught
            log.exception("Error starting bot")

        finally:
            if m and (m.session or m.http.connector):
                # in case we never made it to m.run(), ensure cleanup.
                log.debug("Doing cleanup late.")
                await m.shutdown_cleanup()

            if (not m or not m.init_ok) and not use_certifi:
                if any(sys.exc_info()):
                    # How to log this without redundant messages...
                    print("There are some exceptions that may not have been handled...")
                    traceback.print_exc()
                tryagain = False

            loops += 1

        sleeptime = min(loops * 2, max_wait_time)
        if sleeptime:
            log.info("Restarting in %s seconds...", sleeptime)
            time.sleep(sleeptime)

    print()
    log.info("All done.")
    return exit_signal


if __name__ == "__main__":
    # TODO: we should check / force-change working directory.
    # py3.8 made ProactorEventLoop default on windows.
    # Now we need to make adjustments for a bug in aiohttp :)
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        exit_sig = loop.run_until_complete(main())
    except KeyboardInterrupt:
        # TODO: later this will probably get more cleanup so we can
        # close other things more proper like too.
        log.info("Caught a keyboard interrupt signal.")
        shutdown_loggers()
        rotate_log_files()
        raise

    if exit_sig:
        if isinstance(exit_sig, RestartSignal):
            if exit_sig.get_name() == "RESTART_FULL":
                respawn_bot_process()
            elif exit_sig.get_name() == "RESTART_UPGRADE_ALL":
                PIP.run_upgrade_requirements()
                GIT.run_upgrade_pull()
                respawn_bot_process()
            elif exit_sig.get_name() == "RESTART_UPGRADE_PIP":
                PIP.run_upgrade_requirements()
                respawn_bot_process()
            elif exit_sig.get_name() == "RESTART_UPGRADE_GIT":
                GIT.run_upgrade_pull()
                respawn_bot_process()
        elif isinstance(exit_sig, TerminateSignal):
            shutdown_loggers()
            rotate_log_files()
            sys.exit(exit_sig.exit_code)
