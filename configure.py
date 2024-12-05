#!/usr/bin/env python3

import json
import re
import sys
import textwrap
from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Set

try:
    import curses
    from curses import textpad
except Exception as e1:
    if sys.platform.startswith("win"):
        import subprocess

        try:
            print("You need to install the window-curses pip package.")
            print("Please wait while we try automatically...\n")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-U", "windows-curses"],
            )
            print("Trying to restart python / this tool...")
            subprocess.Popen(  # pylint: disable=consider-using-with
                [sys.executable] + sys.argv,
                creationflags=subprocess.CREATE_NEW_CONSOLE,  # type: ignore[attr-defined]
            )
        except Exception as e2:
            raise e2 from e1
    raise e1

from musicbot import parse_write_base_arg, write_path
from musicbot.aliases import Aliases
from musicbot.bot import MusicBot
from musicbot.config import Config, ConfigOption
from musicbot.constants import (
    DATA_FILE_SERVERS,
    DATA_GUILD_FILE_OPTIONS,
    DEFAULT_COMMAND_ALIAS_FILE,
    DEFAULT_DATA_DIR,
    DEFAULT_OPTIONS_FILE,
    DEFAULT_PERMS_FILE,
)
from musicbot.permissions import Permissions

# Constants
KEY_ESCAPE = 27
KEY_FTAB = ord("\t")
KEY_RETURN = ord("\n")
KEYS_NAV_PREV = [curses.KEY_LEFT, curses.KEY_UP, curses.KEY_BTAB]
KEYS_NAV_NEXT = [curses.KEY_RIGHT, curses.KEY_DOWN, KEY_FTAB]
KEYS_ENTER = [KEY_RETURN, curses.KEY_ENTER]

# Mode constants are duplicated for easier reading in later code.
MODE_PICK_EDITOR = 0
MODE_PICK_ALIAS = 1
MODE_PICK_SERVER = 1
MODE_PICK_SECTION = 1
MODE_PICK_GROUP = 1
MODE_PICK_OPTION = 2
MODE_PICK_FIELD = 2
MODE_EDIT_OPTION = 3
MODE_EDIT_FIELD = 3


class ServerData:
    """
    Represents a single discord server's options.json data.
    """

    def __init__(self, guild_id: str, guild_name: Optional[str]) -> None:
        """
        Create a server data object and load in the options data.
        """
        self.id = guild_id
        if isinstance(guild_name, str):
            self.name = guild_name
        else:
            self.name = "[Unknown]"
        self.known = bool(guild_name)
        self.edited = False
        self.path = write_path(DEFAULT_DATA_DIR).joinpath(
            guild_id, DATA_GUILD_FILE_OPTIONS
        )
        self._options: Dict[str, Any] = {}
        self.load()

    @property
    def has_options(self) -> bool:
        """Test if the server has a data file."""
        return self.path.is_file()

    def __hash__(self) -> int:
        return int(self.id)

    def set(self, option: str, value: Any) -> None:
        """Set the server option value to the given value."""
        self._options[option] = value
        self.edited = True

    def get(self, option: str, default: str) -> Any:
        """Get a server option value or return the given default."""
        return self._options.get(option, default)

    def load(self) -> None:
        """Read the options.json file."""
        parsed: Dict[str, Any] = {}
        if not self.path.is_file():
            self._options = parsed
            return
        with open(self.path, "r", encoding="utf8") as fh:
            parsed = json.load(fh)
            if not isinstance(parsed, dict):
                raise TypeError("Parsed information must be of type Dict[str, Any]")
        self.edited = False
        self._options = parsed

    def save(self) -> None:
        """Save the options.json file"""
        with open(self.path, "w", encoding="utf8") as fh:
            json.dump(self._options, fh)
        self.edited = False


class ConfigAssistantTextSystem:
    """
    An ncurses application for messing with configs.
    CATs for short.
    """

    def __init__(self, stdscr: curses.window) -> None:
        """
        The CATS initializer which starts CATS.
        Should be called form curses.wrapper()
        """
        self.scr = stdscr
        self.win = curses.newwin(
            curses.LINES - 3,  # pylint: disable=no-member
            curses.COLS,  # pylint: disable=no-member
            3,
            0,
        )

        # turn off the cursor
        curses.curs_set(0)
        # set escape delay to 100 ms
        curses.set_escdelay(100)  # type: ignore[attr-defined]
        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(10, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(11, curses.COLOR_RED, curses.COLOR_WHITE)
        curses.init_pair(12, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(13, curses.COLOR_YELLOW, curses.COLOR_WHITE)
        curses.init_pair(14, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(15, curses.COLOR_BLUE, curses.COLOR_WHITE)

        # set up editor selection and mode vars.
        self.edit_error_msg = ""
        self.edit_mode = MODE_PICK_EDITOR
        self.sct_selno = 0
        self.opt_selno = 0

        # Managers / buffers for editor data.
        self.mgr_alias: Optional[Aliases] = None
        self.mgr_perms: Optional[Permissions] = None
        self.mgr_opts: Optional[Config] = None
        self.mgr_srvs: List[ServerData] = []
        self.edited_opts: Set[ConfigOption] = set()
        self.edited_perms: Set[ConfigOption] = set()
        self.edited_aliases: Set[str] = set()

        # store valid commands from musicbot.
        self.top_commands: Set[str] = set()
        self.sub_commands: DefaultDict[str, Set[str]] = defaultdict(set)
        self.sub_cmd_pattern = re.compile(r"^{prefix}[a-z]+\s{1}([a-z0-9]+)", re.I)
        self._get_natural_commands()

        self.main_screen()

    def _get_natural_commands(self) -> None:
        """
        Loops over MusicBot's attributes and extracts a set of commands
        which are avaialble in `self.top_commands`.
        """
        for attr in dir(MusicBot):
            if attr.startswith("cmd_"):
                cmd_name = attr.replace("cmd_", "")
                # attempt to get sub-commands from usage strings.
                cmd = getattr(MusicBot, attr, None)
                if cmd:
                    self._get_sub_commands(cmd)
                    self.top_commands.add(cmd_name)

    def _get_sub_commands(self, cmd: Callable[..., Any]) -> None:
        """
        Takes a valid command attribute from musicbot then extracts possible
        sub-commands from the usage stirngs.
        The results are available in self.sub_commands as a dictionary of sets.
        """
        usage = getattr(cmd, "help_usage", [])
        cmd_name = cmd.__name__.replace("cmd_", "")
        for ustr in usage:
            ulines = ustr.split("\n")
            for uline in ulines:
                m = self.sub_cmd_pattern.match(uline)
                if m:
                    self.sub_commands[cmd_name].add(m.group(1))

    def get_text_input(
        self, lines: int, cols: int, y: int, x: int, value: str = ""
    ) -> str:
        """
        Create a single-line text input with optional value for editing.
        Value is returned with leading and trailing space removed.
        """
        curses.curs_set(1)
        twin = curses.newwin(lines, cols, y, x)
        twin.addstr(0, 0, value)
        tpad = textpad.Textbox(twin, insert_mode=True)
        tpad.stripspaces = False
        t = tpad.edit().strip()
        curses.curs_set(0)
        return t

    def do_key_nav(
        self,
        max_scts: int,
        max_opts: int,
        save_callback: Callable[..., None],
        reload_callback: Callable[..., None],
        remove_callback: Optional[Callable[..., None]] = None,
        add_callback: Optional[Callable[..., None]] = None,
    ) -> bool:
        """
        Handle user inputs via curses key input method.
        This usually gets skipped when text-input is active.
        """
        key = self.scr.getch()

        def empty() -> None:
            return

        if remove_callback is None:
            remove_callback = empty
        if add_callback is None:
            add_callback = empty

        # select previous
        if key in KEYS_NAV_PREV:
            self.edit_error_msg = ""
            if self.edit_mode == MODE_PICK_OPTION:
                if self.opt_selno > 0:
                    self.opt_selno -= 1
                else:
                    self.opt_selno = max_opts
            elif self.edit_mode == MODE_PICK_SECTION:
                if self.sct_selno > 0:
                    self.sct_selno -= 1
                else:
                    self.sct_selno = max_scts

        # select next
        elif key in KEYS_NAV_NEXT:
            self.edit_error_msg = ""
            if self.edit_mode == MODE_PICK_OPTION:
                if self.opt_selno < max_opts:
                    self.opt_selno += 1
                else:
                    self.opt_selno = 0
            elif self.edit_mode == MODE_PICK_SECTION:
                if self.sct_selno < max_scts:
                    self.sct_selno += 1
                else:
                    self.sct_selno = 0

        # confirm selection
        elif key in KEYS_ENTER:
            self.edit_error_msg = ""
            # picking aliases
            if self.edit_mode == MODE_PICK_SECTION:
                self.edit_mode = MODE_PICK_OPTION
                self.opt_selno = 0
            # picking alias component fields
            elif self.edit_mode == MODE_PICK_OPTION:
                self.edit_mode = MODE_EDIT_OPTION

        # Add data
        elif key == curses.KEY_F8:
            add_callback()

        # Remove data
        elif key == curses.KEY_F7:
            remove_callback()

        # Reload data
        elif key == curses.KEY_F5:
            reload_callback()

        # Save data
        elif key == curses.KEY_F2:
            save_callback()

        # Go back
        elif key == KEY_ESCAPE:
            if self.edit_mode == MODE_PICK_SECTION:
                self.opt_selno = 0
                self.sct_selno = 0
                return True
            if self.edit_mode == MODE_PICK_OPTION:
                self.edit_mode = MODE_PICK_SECTION
                self.opt_selno = 0

        # handle resize
        elif key == curses.KEY_RESIZE:
            ny, nx = self.scr.getmaxyx()
            curses.resize_term(ny, nx)
            curses.update_lines_cols()
            self.win.resize(ny - 3, nx)
            self.scr.refresh()
            self.win.refresh()

        return False

    def select_cmd_perms(self, cur_val: Set[str]) -> str:
        """Special input method use for Permissions command list options."""
        perms = list(self.top_commands)
        max_px = 0
        for cmd, subs in self.sub_commands.items():
            for sub in subs:
                perm = f"{cmd}_{sub}"
                perms.append(perm)
                max_px = max(max_px, len(perm))

        perms = sorted(perms)
        selno = 0
        selected: Set[str] = cur_val

        maxy, maxx = self.scr.getmaxyx()
        padx = 6
        midx = (maxx - 1) // 2
        midwx = midx - ((max_px + padx) // 2)
        win = curses.newwin(maxy - 4, max_px + padx, 3, midwx)
        win.clear()
        win.refresh()
        self.scr.refresh()
        while True:
            maxy, maxx = self.scr.getmaxyx()
            win.clear()
            win.box()
            win.addstr(1, 1, "Select Commands:", curses.A_BOLD)
            hud = "[SPACE] Select  [ENTER] Confirm Selected  [ESC] Go Back"
            self.scr.addstr(
                maxy - 1,
                0,
                hud.center(maxx - 1),
                curses.color_pair(1) | curses.A_BOLD,
            )

            viewno = max(0, (selno - (maxy - 7)) + 1)
            view = list(perms)[viewno : viewno + (maxy - 7)]
            for i, perm in enumerate(view):
                flags = 0
                if i + viewno == selno:
                    flags = curses.color_pair(1)
                if perm in selected:
                    win.addstr(i + 2, 1, f"[x] {perm}", flags)
                else:
                    win.addstr(i + 2, 1, f"[ ] {perm}", flags)

            win.refresh()
            self.scr.refresh()

            key = self.scr.getch()
            if key == KEY_ESCAPE:
                break
            if key in KEYS_ENTER:
                return " ".join(sorted(list(selected)))
            if key in KEYS_NAV_NEXT:
                if selno < len(perms) - 1:
                    selno += 1
                else:
                    selno = 0
            elif key in KEYS_NAV_PREV:
                if selno > 0:
                    selno -= 1
                else:
                    selno = len(perms) - 1
            elif key == ord(" "):
                perm = list(perms)[selno]
                if perm in selected:
                    selected.discard(perm)
                else:
                    selected.add(perm)
        return ""

    def main_screen(self) -> None:
        """Process the CATS main menu screen."""
        # Create a list of config types to manage.
        config_files = {
            "Options": "Manage settings saved in options.ini file.",
            "Permissions": "Manage groups saved in permissions.ini file.",
            "Aliases": "Manage aliases saved in aliases.json file.",
            "Servers": "Manage per-server settings saved in data files.",
        }
        config_types = list(config_files.keys())
        config_edited = [False for _ in config_types]
        config_sel = 0
        selected = False

        while True:
            _max_y, max_x = self.scr.getmaxyx()
            self.scr.clear()
            self.scr.addstr(0, 0, "Select configuration to edit:", curses.A_BOLD)

            # build config selection at top.
            c = 2
            for i, option in enumerate(config_types):
                opt_str = f" {option} "
                flags = 0
                if i == config_sel:
                    flags = curses.color_pair(1)
                    if config_edited[i]:
                        flags = curses.color_pair(15)
                    self.scr.addstr(1, c, opt_str, flags)
                else:
                    if config_edited[i]:
                        flags = curses.color_pair(14)
                    self.scr.addstr(1, c, opt_str, flags)
                c += len(opt_str)
                if config_edited[i]:
                    self.scr.addstr(
                        4, 2, "You have unsaved edits!", curses.color_pair(14)
                    )
            self.scr.hline(2, 0, curses.ACS_HLINE, max_x)
            self.scr.addstr(3, 2, config_files[config_types[config_sel]])

            # Get user input
            key = self.scr.getch()
            if key in KEYS_NAV_PREV:
                if config_sel > 0:
                    config_sel -= 1
                else:
                    config_sel = len(config_types) - 1
            elif key in KEYS_NAV_NEXT:
                if config_sel < len(config_types) - 1:
                    config_sel += 1
                else:
                    config_sel = 0
            elif key in KEYS_ENTER and not selected:
                selected = True
            elif key == KEY_ESCAPE:
                selected = False
                if any(x for x in config_edited):
                    self.scr.addstr(
                        4, 2, "You have unsaved edits!", curses.color_pair(10)
                    )
                    self.scr.addstr(
                        5,
                        2,
                        "Press [ESC] again to exit anyway.",
                        curses.color_pair(10) | curses.A_BOLD,
                    )
                    key = self.scr.getch()
                    if key == KEY_ESCAPE:
                        break
                else:
                    break

            if selected:
                # enter Options editor
                if config_sel == 0:
                    self.edit_mode = MODE_PICK_SECTION
                    config_edited[0] = self.config_options()
                    selected = False

                # enter Permissions editor
                elif config_sel == 1:
                    self.edit_mode = MODE_PICK_GROUP
                    config_edited[1] = self.config_permissions()
                    selected = False

                # enter Aliases editor
                elif config_sel == 2:
                    self.edit_mode = MODE_PICK_ALIAS
                    config_edited[2] = self.config_aliases()
                    selected = False

                # enter Server options editor.
                elif config_sel == 3:
                    self.edit_mode = MODE_PICK_SERVER
                    config_edited[3] = self.config_servers()
                    selected = False

            self.scr.refresh()

    def config_options(self) -> bool:
        """Run CATS in options editing mode."""
        if not self.mgr_opts:
            self.mgr_opts = Config(write_path(DEFAULT_OPTIONS_FILE))
        sections = self.mgr_opts.parser.sections()

        edit_buffer = ""

        missing_options: Dict[str, List[str]] = defaultdict(list)
        for mopt in self.mgr_opts.register.ini_missing_options:
            missing_options[mopt.section].append(mopt.option)

        def save_callback() -> None:
            eopts = list(self.edited_opts)
            if not self.mgr_opts:
                return
            for eopt in eopts:
                if self.mgr_opts.save_option(eopt):
                    self.edited_opts.discard(eopt)

        def reload_callback() -> None:
            nonlocal sections
            self.mgr_opts = Config(write_path(DEFAULT_OPTIONS_FILE))
            sections = self.mgr_opts.parser.sections()
            self.edited_opts.clear()
            missing_options.clear()
            for mopt in self.mgr_opts.register.ini_missing_options:
                missing_options[mopt.section].append(mopt.option)

        while True:
            # setup the window for this frame.
            max_y, max_x = self.win.getmaxyx()
            self.win.clear()

            # update selected section
            selected_sct: str = sections[self.sct_selno]

            # Layout window.
            self.win.hline(2, 0, curses.ACS_HLINE, max_x)
            self.win.vline(2, 30, curses.ACS_VLINE, max_y)
            self.win.addch(2, 30, curses.ACS_TTEE)
            if self.edit_error_msg:
                self.win.addstr(0, 1, self.edit_error_msg, curses.color_pair(12))
            else:
                self.win.addstr(0, 1, "Select a section and option to edit.")
            self.win.addstr(1, 1, "Section:", curses.A_BOLD)
            self.win.addstr(1, 10, "[", curses.A_DIM)
            if self.edit_mode == MODE_PICK_SECTION:
                self.win.addstr(1, 11, selected_sct, curses.color_pair(1))
            else:
                self.win.addstr(1, 11, selected_sct)
            self.win.addstr(1, 11 + len(selected_sct), "]", curses.A_DIM)

            # Show HUD
            hud = " [F2] Save  [F5] Reload  [ESC] Go Back"
            pad = max_x - len(hud) - 31
            hud += " " * pad
            self.win.addstr(
                max_y - 1, 31, hud[: max_x - 32], curses.color_pair(1) | curses.A_BOLD
            )

            # build options from the above selected section
            options = (
                self.mgr_opts.parser.options(selected_sct)
                + missing_options[selected_sct]
            )
            selected_opt = self.mgr_opts.register.get_config_option(
                selected_sct, options[self.opt_selno]
            )
            opt_viewno = max(0, (self.opt_selno - (max_y - 3)) + 1)
            visopts = options[opt_viewno : opt_viewno + (max_y - 3)]
            cnf_opt: Optional[ConfigOption] = None
            for i, opt in enumerate(visopts):
                cnf_opt = self.mgr_opts.register.get_config_option(selected_sct, opt)
                if (
                    i + opt_viewno == self.opt_selno
                    and self.edit_mode == MODE_PICK_OPTION
                ):
                    flags = curses.color_pair(1)
                    # If register returns None, the option does not exist.
                    if cnf_opt is None:
                        flags = curses.color_pair(11)
                    if cnf_opt in self.edited_opts:
                        flags = curses.color_pair(15)
                    # If opt is listed in missing_options, mark it so.
                    elif opt in missing_options[selected_sct]:
                        flags = curses.color_pair(13)
                    self.win.addstr(i + 3, 0, f" {opt[:28]} ", flags)
                else:
                    flags = 0
                    if cnf_opt is None:
                        flags = curses.color_pair(10)
                    if cnf_opt in self.edited_opts:
                        flags = curses.color_pair(14)
                    elif opt in missing_options[selected_sct]:
                        flags = curses.color_pair(12)
                    self.win.addstr(i + 3, 0, f" {opt[:28]} ", flags)

            # build info for selected option.
            if selected_opt:
                max_desc_x = max_x - 34
                # vals = mgr.register.get_values(selected_opt)
                comment = selected_opt.comment
                if selected_opt.comment_args:
                    comment %= selected_opt.comment_args
                comment_lines = []
                for line in comment.split("\n"):
                    if len(line) > max_desc_x:
                        ls = textwrap.wrap(line, width=max_desc_x)
                        comment_lines += ls
                    else:
                        comment_lines.append(line)

                lbl_option = "Option:"
                lbl_default = "Default Setting:"
                lbl_current = "Current Setting:"
                lbl_desc = "Description:"

                # option name
                self.win.addstr(3, 31, lbl_option, curses.A_BOLD)
                self.win.addstr(3, 32 + len(lbl_option), selected_opt.option)

                # default value
                dval = self.mgr_opts.register.to_ini(selected_opt, use_default=True)
                self.win.addstr(4, 31, lbl_default, curses.A_BOLD)
                self.win.addstr(4, 32 + len(lbl_default), dval)

                # current setting
                cval = self.mgr_opts.register.to_ini(selected_opt)
                self.win.addstr(5, 31, lbl_current, curses.A_BOLD)
                # win.addstr(5, 32 + len(lbl_current), str(vals))
                if selected_opt.option in missing_options[selected_sct]:
                    self.win.addstr(
                        5,
                        33 + len(lbl_current),
                        "This option is missing from your INI file.",
                        curses.color_pair(12),
                    )
                cflags = 0
                if len(cval) >= 199:
                    cflags = curses.color_pair(12)
                if len(cval) <= max_desc_x:
                    self.win.addstr(6, 33, cval, cflags)
                    last_y = 7
                else:
                    cval_lines = textwrap.wrap(cval, width=max_desc_x)
                    for i, line in enumerate(cval_lines):
                        y = 6 + i
                        self.win.addstr(y, 33, line, cflags)
                        last_y = y + 1

                # description
                self.win.addstr(last_y + 1, 31, lbl_desc, curses.A_BOLD)
                for i, line in enumerate(comment_lines):
                    self.win.addstr(last_y + 2 + i, 33, line)

            # display a message for non-existing options.
            else:
                self.win.addstr(4, 33, "This option is invalid.", curses.A_BOLD)
                self.win.addstr(5, 33, "It can be removed from your INI file.")

            self.win.refresh()

            # handle getting the edited string.
            edit_buffer = ""
            if self.edit_mode == MODE_EDIT_OPTION:
                if selected_opt is None:
                    self.win.addstr(
                        6, 33, "You cannot edit this option.", curses.color_pair(10)
                    )
                    self.edit_mode = MODE_PICK_OPTION
                else:
                    # TODO: Maybe add ConfigOption var for input length.
                    edit_buffer = self.get_text_input(1, 200, 9, 33)
                    last_ini_val = self.mgr_opts.register.to_ini(selected_opt)
                    self.edit_mode = MODE_PICK_OPTION
                    self.edit_error_msg = ""
                    no_error = self.mgr_opts.update_option(selected_opt, edit_buffer)
                    cur_ini_val = self.mgr_opts.register.to_ini(selected_opt)
                    if not no_error or cur_ini_val == last_ini_val:
                        self.edit_error_msg = (
                            f"The option was not updated: {selected_opt.option}"
                        )
                    else:
                        self.edited_opts.add(selected_opt)

            self.win.refresh()

            # get this frame's key code input, if we didn't just leave edit mode.
            if not edit_buffer:
                goback = self.do_key_nav(
                    len(sections) - 1,
                    len(options) - 1,
                    save_callback,
                    reload_callback,
                )
                if goback:
                    break

        return bool(self.edited_opts)

    def config_permissions(self) -> bool:
        """Run CATS in Permissions editing mode."""
        if not self.mgr_perms:
            self.mgr_perms = Permissions(write_path(DEFAULT_PERMS_FILE))

        groups = self.mgr_perms.config.sections()

        selected_group: str = ""
        selected_opt: Optional[ConfigOption] = None
        edit_buffer: str = ""

        missing_options: Dict[str, List[str]] = defaultdict(list)
        for mopt in self.mgr_perms.register.ini_missing_options:
            missing_options[mopt.section].append(mopt.option)

        def save_callback() -> None:
            if self.mgr_perms is None:
                return
            saved_groups: Set[str] = set()
            opts = list(self.edited_perms)
            for eopt in opts:
                if eopt.section not in saved_groups:
                    self.mgr_perms.save_group(eopt.section)
                self.edited_perms.discard(eopt)
            reload_callback()

        def reload_callback() -> None:
            nonlocal groups
            self.mgr_perms = Permissions(write_path(DEFAULT_PERMS_FILE))
            groups = self.mgr_perms.config.sections()
            self.edited_perms.clear()
            missing_options.clear()
            for mopt in self.mgr_perms.register.ini_missing_options:
                missing_options[mopt.section].append(mopt.option)
            if self.sct_selno >= len(groups):
                self.sct_selno = 0

        def remove_callback() -> None:
            nonlocal selected_opt
            if self.mgr_perms is None or selected_opt is None:
                return
            self.mgr_perms.remove_group(selected_opt.section)
            self.edited_perms.add(selected_opt)

        def add_callback() -> None:
            nonlocal groups
            if not self.mgr_perms:
                return
            self.win.clear()
            self.win.addstr(0, 1, "Enter a name for the new group:", curses.A_BOLD)
            self.win.addstr(1, 1, " " * (max_x - 2))
            self.win.refresh()
            new_name = self.get_text_input(1, 40, 4, 1)
            self.mgr_perms.add_group(new_name)
            self.mgr_perms.save_group(new_name)
            reload_callback()
            self.sct_selno = groups.index(new_name)

        while True:
            # setup the window for this frame.
            max_y, max_x = self.win.getmaxyx()
            self.win.clear()

            # update selected section
            selected_group = groups[self.sct_selno]

            # Layout window.
            self.win.hline(2, 0, curses.ACS_HLINE, max_x)
            self.win.vline(2, 30, curses.ACS_VLINE, max_y)
            self.win.addch(2, 30, curses.ACS_TTEE)
            if self.edit_error_msg:
                self.win.addstr(0, 1, self.edit_error_msg, curses.color_pair(12))
            else:
                self.win.addstr(0, 1, "Select a group and option to edit.")
            self.win.addstr(1, 1, "Group:", curses.A_BOLD)
            self.win.addstr(1, 10, "[", curses.A_DIM)
            if self.edit_mode == MODE_PICK_SECTION:
                self.win.addstr(1, 11, selected_group, curses.color_pair(1))
            else:
                self.win.addstr(1, 11, selected_group)
            self.win.addstr(1, 11 + len(selected_group), "]", curses.A_DIM)

            # Show HUD
            hud = " [F2] Save  [F5] Reload  [F7] Remove Group  [F8] Add Group  [ESC] Go Back"
            pad = max_x - len(hud) - 31
            hud += " " * pad
            self.win.addstr(
                max_y - 1, 31, hud[: max_x - 32], curses.color_pair(1) | curses.A_BOLD
            )

            # build options from the above selected section
            options = (
                self.mgr_perms.config.options(selected_group)
                + missing_options[selected_group]
            )
            selected_opt = self.mgr_perms.register.get_config_option(
                selected_group, options[self.opt_selno]
            )
            opt_viewno = max(0, (self.opt_selno - (max_y - 3)) + 1)
            visopts = options[opt_viewno : opt_viewno + (max_y - 3)]
            cnf_opt: Optional[ConfigOption] = None
            for i, opt in enumerate(visopts):
                cnf_opt = self.mgr_perms.register.get_config_option(selected_group, opt)
                if (
                    i + opt_viewno == self.opt_selno
                    and self.edit_mode == MODE_PICK_OPTION
                ):
                    flags = curses.color_pair(1)
                    # If register returns None, the option does not exist.
                    if cnf_opt is None:
                        flags = curses.color_pair(11)
                    if cnf_opt in self.edited_perms:
                        flags = curses.color_pair(15)
                    self.win.addstr(i + 3, 0, f" {opt[:28]} ", flags)
                else:
                    flags = 0
                    if cnf_opt is None:
                        flags = curses.color_pair(10)
                    if cnf_opt in self.edited_perms:
                        flags = curses.color_pair(14)
                    self.win.addstr(i + 3, 0, f" {opt[:28]} ", flags)

            # build info for selected option.
            if selected_opt:
                max_desc_x = max_x - 34
                max_opt_x = max_desc_x
                # vals = mgr.register.get_values(selected_opt)
                comment = selected_opt.comment
                if selected_opt.comment_args:
                    comment %= selected_opt.comment_args
                comment_lines = []
                for line in comment.split("\n"):
                    if len(line) > max_desc_x:
                        ls = textwrap.wrap(line, width=max_desc_x)
                        comment_lines += ls
                    else:
                        comment_lines.append(line)

                lbl_option = "Option:"
                lbl_default = "Default Setting:"
                lbl_current = "Current Setting:"
                lbl_desc = "Description:"

                # option name
                self.win.addstr(3, 31, lbl_option, curses.A_BOLD)
                self.win.addstr(3, 32 + len(lbl_option), selected_opt.option)

                # default value
                dval = self.mgr_perms.register.to_ini(selected_opt, use_default=True)
                self.win.addstr(4, 31, lbl_default, curses.A_BOLD)
                self.win.addstr(4, 32 + len(lbl_default), dval)

                # current setting
                cval = self.mgr_perms.register.to_ini(selected_opt)
                self.win.addstr(5, 31, lbl_current, curses.A_BOLD)
                # win.addstr(5, 32 + len(lbl_current), str(vals))
                cflags = 0
                if len(cval) >= 199:
                    cflags = curses.color_pair(12)
                if len(cval) <= max_opt_x:
                    self.win.addstr(6, 33, cval, cflags)
                    last_y = 7
                else:
                    cval_lines = textwrap.wrap(cval, width=max_opt_x)
                    for i, line in enumerate(cval_lines):
                        y = 6 + i
                        self.win.addstr(y, 33, line, cflags)
                        last_y = y + 1

                # description
                self.win.addstr(last_y + 1, 31, lbl_desc, curses.A_BOLD)
                for i, line in enumerate(comment_lines):
                    self.win.addstr(last_y + 2 + i, 33, line)

            # display a message for non-existing options.
            else:
                self.win.addstr(4, 33, "This option is invalid.", curses.A_BOLD)
                self.win.addstr(5, 33, "It can be removed from your INI file.")

            self.win.refresh()

            # handle getting the edited string.
            edit_buffer = ""
            if self.edit_mode == MODE_EDIT_OPTION:
                if selected_opt is None:
                    self.win.addstr(
                        6, 33, "You cannot edit this option.", curses.color_pair(10)
                    )
                    self.edit_mode = MODE_PICK_OPTION
                else:
                    rawval = self.mgr_perms.register.get_values(selected_opt)[0]
                    if selected_opt.option in [
                        "CommandWhitelist",
                        "CommandBlacklist",
                    ]:
                        edit_buffer = self.select_cmd_perms(rawval)  # type: ignore[arg-type]
                    else:
                        # TODO: Maybe add ConfigOption var for input length.
                        edit_buffer = self.get_text_input(1, 200, 9, 33, cval)
                    last_ini_val = self.mgr_perms.register.to_ini(selected_opt)
                    self.edit_mode = MODE_PICK_OPTION
                    self.edit_error_msg = ""
                    no_error = self.mgr_perms.update_option(selected_opt, edit_buffer)
                    cur_ini_val = self.mgr_perms.register.to_ini(selected_opt)
                    if not no_error or cur_ini_val == last_ini_val:
                        self.edit_error_msg = (
                            f"The option was not updated: {selected_opt.option}"
                        )
                    else:
                        self.edited_perms.add(selected_opt)

            self.win.refresh()

            # get this frame's key code input, if we didn't just leave edit mode.
            if not edit_buffer:
                goback = self.do_key_nav(
                    len(groups) - 1,
                    len(options) - 1,
                    save_callback,
                    reload_callback,
                    remove_callback,
                    add_callback,
                )
                if goback:
                    break

        return bool(self.edited_perms)

    def config_aliases(self) -> bool:
        """Run CATS in Alias editing mode."""
        if not self.mgr_alias:
            self.mgr_alias = Aliases(write_path(DEFAULT_COMMAND_ALIAS_FILE), [])

        # Set up vars and selection list.
        aliases = []
        edit_buffer = ""
        new_alias_name = ""

        def get_alias_list(mgr: Aliases) -> List[str]:
            return ["[New]"] + sorted(mgr.aliases.keys())

        def save_callback() -> None:
            if self.mgr_alias:
                self.mgr_alias.save()
                self.edited_aliases.clear()

        def reload_callback() -> None:
            if self.mgr_alias:
                self.mgr_alias.load()
                self.edited_aliases.clear()

        # run output/update loop.
        while True:
            # setup the window for this frame.
            max_y, max_x = self.win.getmaxyx()
            self.win.clear()
            self.win.vline(0, 14, curses.ACS_VLINE, max_y)
            self.scr.addch(2, 14, curses.ACS_TTEE)

            # Show HUD
            hud = " [F2] Save  [F5] Reload  [ESC] Go Back"
            pad = max_x - len(hud) - 16
            hud += " " * pad
            self.win.addstr(
                max_y - 1, 15, hud[: max_x - 16], curses.color_pair(1) | curses.A_BOLD
            )

            # build the selection for this "frame"
            aliases = get_alias_list(self.mgr_alias)
            alias_viewno = max(0, (self.sct_selno - max_y) + 1)
            visible = aliases[alias_viewno : alias_viewno + max_y]
            selected_alias = ""
            selected_cmd = None
            for i, alias in enumerate(visible):
                flags = 0
                if i + alias_viewno == 0:
                    cmd = None
                    flags |= curses.A_BOLD
                else:
                    cmd = self.mgr_alias.aliases[alias]

                if self.sct_selno == i + alias_viewno:
                    selected_alias = alias
                    selected_cmd = cmd
                    flags = curses.color_pair(1)
                    if alias in self.edited_aliases:
                        flags = curses.color_pair(15)
                    self.win.addstr(i, 0, f" {alias[:11]} ", flags)
                else:
                    if alias in self.edited_aliases:
                        flags = curses.color_pair(14)
                    self.win.addstr(i, 0, f" {alias[:11]} ", flags)

            # build info display for selected alias.
            if selected_cmd or self.edit_mode in [MODE_PICK_FIELD, MODE_EDIT_FIELD]:
                # placeholders for edit mode should be one space when empty.
                p_alias = new_alias_name or selected_alias or " "
                p_cmd = " "
                if selected_cmd and selected_cmd[0]:
                    p_cmd = selected_cmd[0]
                p_args = " "
                if selected_cmd and selected_cmd[1]:
                    p_args = selected_cmd[1]

                # Alias field
                self.win.addstr(0, 15, "Alias:", curses.A_BOLD)
                if self.edit_mode == MODE_PICK_FIELD and self.opt_selno == 0:
                    self.win.addstr(1, 17, p_alias, curses.color_pair(1))
                else:
                    self.win.addstr(1, 17, p_alias)

                # Command field
                lbl_cmd = "Command:"
                self.win.addstr(2, 15, lbl_cmd, curses.A_BOLD)
                if p_cmd not in self.top_commands:
                    self.win.addstr(
                        2,
                        16 + len(lbl_cmd),
                        "Invalid command name",
                        curses.color_pair(10),
                    )
                if self.edit_mode == MODE_PICK_FIELD and self.opt_selno == 1:
                    self.win.addstr(3, 17, p_cmd, curses.color_pair(1))
                else:
                    self.win.addstr(3, 17, p_cmd)

                # Arguments field.
                if (selected_cmd and selected_cmd[1]) or self.edit_mode in [
                    MODE_PICK_FIELD,
                    MODE_EDIT_FIELD,
                ]:
                    self.win.addstr(4, 15, "Arguments:", curses.A_BOLD)
                    if self.edit_mode == MODE_PICK_FIELD and self.opt_selno == 2:
                        self.win.addstr(5, 17, p_args, curses.color_pair(1))
                    else:
                        self.win.addstr(5, 17, p_args)

            # display a simple message before "New" is edited.
            else:
                self.opt_selno = 0
                self.win.addstr(0, 15, "Add a new command alias.")

            self.win.refresh()

            # handle getting the edited string.
            edit_buffer = ""
            if self.edit_mode == MODE_EDIT_FIELD:
                edit_cmd = selected_cmd
                if not edit_cmd:
                    edit_cmd = ("", "")

                # edited alias name
                if self.opt_selno == 0:
                    edit_buffer = self.get_text_input(1, 20, 4, 17)
                    if edit_buffer:
                        self.edited_aliases.add(edit_buffer)
                        # save new alias name to buffer and move to command field.
                        if self.sct_selno == 0:
                            new_alias_name = edit_buffer
                            self.opt_selno = 1
                        else:
                            # update aliases
                            self.mgr_alias.remove_alias(selected_alias)
                            self.mgr_alias.make_alias(
                                edit_buffer, edit_cmd[0], edit_cmd[1]
                            )

                            # get the new index value.
                            aliases = get_alias_list(self.mgr_alias)
                            self.sct_selno = aliases.index(edit_buffer)
                            self.edit_mode = MODE_PICK_FIELD
                    else:
                        self.edit_mode = MODE_PICK_FIELD

                # edited command name
                elif self.opt_selno == 1:
                    edit_buffer = self.get_text_input(1, 20, 6, 17)
                    if edit_buffer:
                        if new_alias_name:
                            self.mgr_alias.make_alias(new_alias_name, edit_buffer, "")
                            # get the new index value.
                            aliases = get_alias_list(self.mgr_alias)
                            self.sct_selno = aliases.index(new_alias_name)
                            new_alias_name = ""
                        else:
                            self.mgr_alias.make_alias(
                                selected_alias, edit_buffer, edit_cmd[1]
                            )
                            self.edited_aliases.add(selected_alias)
                    self.edit_mode = MODE_PICK_FIELD

                # edited arguments field
                elif self.opt_selno == 2:
                    edit_buffer = self.get_text_input(1, 60, 8, 17)
                    self.edited_aliases.add(selected_alias)
                    self.mgr_alias.make_alias(selected_alias, edit_cmd[0], edit_buffer)
                    self.edit_mode = MODE_PICK_FIELD

            self.win.refresh()

            # get this frame's key code input, if we didn't just leave edit mode.
            if not edit_buffer:
                goback = self.do_key_nav(
                    len(aliases) - 1,
                    2,
                    save_callback,
                    reload_callback,
                )
                if goback:
                    break

        return bool(self.edited_aliases)

    def config_servers(self) -> bool:
        """Run CATS in Server Data editing mode."""
        data_path = write_path(DEFAULT_DATA_DIR)
        servers_path = data_path.joinpath(DATA_FILE_SERVERS)
        opt_pattern = "*/"

        def get_servers() -> List[ServerData]:
            # known servers have entries in data/server txt
            srvs: Dict[str, ServerData] = {}
            names: Dict[str, str] = {}
            if servers_path.is_file():
                slines = servers_path.read_text(encoding="utf8").split("\n")
                for line in slines:
                    line = line.strip()
                    if not line:
                        continue

                    bits = line.split(": ", maxsplit=1)
                    gid = bits[0]
                    sname = bits[1]
                    names[gid] = sname
                    srvs[gid] = ServerData(gid, sname)

            for path in data_path.glob(opt_pattern):
                if not path.is_dir():
                    continue
                gid = path.name
                name: Optional[str] = names.get(gid, None)
                srvs[gid] = ServerData(gid, name)

            return list(srvs.values())

        if not self.mgr_srvs:
            self.mgr_srvs = get_servers()

        edit_buffer = ""
        selected_srv = self.mgr_srvs[0]
        while True:
            # setup the window for this frame.
            max_y, max_x = self.win.getmaxyx()
            self.win.clear()
            # Layout window.
            self.win.hline(1, 0, curses.ACS_HLINE, max_x)
            self.win.vline(1, 15, curses.ACS_VLINE, max_y)
            self.win.addch(1, 15, curses.ACS_TTEE)

            # Show HUD
            hud = " [F2] Save  [F5] Reload  [ESC] Go Back"
            pad = max_x - len(hud) - 16
            hud += " " * pad
            self.win.addstr(
                max_y - 1, 16, hud[: max_x - 17], curses.color_pair(1) | curses.A_BOLD
            )

            # build the selection for this "frame"
            srv_viewno = max(0, (self.sct_selno - max_y) + 1)
            visible = self.mgr_srvs[srv_viewno : srv_viewno + max_y]
            for i, srv in enumerate(visible):
                flags = 0
                if not srv.has_options:
                    flags = curses.A_DIM
                if i + srv_viewno == self.sct_selno:
                    selected_srv = srv
                    flags = curses.color_pair(1)
                    if srv.edited:
                        flags = curses.color_pair(15)
                    self.win.addstr(i + 2, 0, f" {srv.name[:12]} ", flags)
                else:
                    if srv.edited:
                        flags = curses.color_pair(14)
                    self.win.addstr(i + 2, 0, f" {srv.name[:12]} ", flags)

            self.win.addstr(0, 1, f"Select a server to edit. [ID: {selected_srv.id}]")
            self.win.refresh()

            # build info display for selected alias.
            # Command Prefix field
            prefix = selected_srv.get("command_prefix", " ")
            self.win.addstr(2, 16, "Command Prefix:", curses.A_BOLD)
            if self.edit_mode == MODE_PICK_FIELD and self.opt_selno == 0:
                self.win.addstr(3, 18, prefix, curses.color_pair(1))
            else:
                self.win.addstr(3, 18, prefix)

            # Playlist field
            playlist = selected_srv.get("auto_playlist", " ")
            self.win.addstr(4, 16, "Playlist File:", curses.A_BOLD)
            if self.edit_mode == MODE_PICK_FIELD and self.opt_selno == 1:
                self.win.addstr(5, 18, playlist, curses.color_pair(1))
            else:
                self.win.addstr(5, 18, playlist)

            # Language field.
            lang = selected_srv.get("language", " ")
            lang = lang or " "
            self.win.addstr(6, 16, "Language:", curses.A_BOLD)
            if self.edit_mode == MODE_PICK_FIELD and self.opt_selno == 2:
                self.win.addstr(7, 18, lang, curses.color_pair(1))
            else:
                self.win.addstr(7, 18, lang)

            self.win.refresh()

            # handle getting the edited string.
            edit_buffer = ""
            if self.edit_mode == MODE_EDIT_FIELD:
                # edited command prefix
                if self.opt_selno == 0:
                    edit_buffer = self.get_text_input(1, 20, 6, 18)
                    selected_srv.set("command_prefix", edit_buffer)
                    self.edit_mode = MODE_PICK_FIELD

                # edited auto playlist
                elif self.opt_selno == 1:
                    edit_buffer = self.get_text_input(1, 60, 8, 18)
                    if edit_buffer:
                        selected_srv.set("auto_playlist", edit_buffer)
                    else:
                        selected_srv.set("auto_playlist", None)
                    self.edit_mode = MODE_PICK_FIELD

                # edited arguments field
                elif self.opt_selno == 2:
                    edit_buffer = self.get_text_input(1, 20, 10, 18)
                    selected_srv.set("language", edit_buffer)
                    self.edit_mode = MODE_PICK_FIELD

            # get this frame's key code input, if we didn't just leave edit mode.
            if not edit_buffer:
                goback = self.do_key_nav(
                    len(self.mgr_srvs) - 1,
                    2,
                    selected_srv.save,
                    selected_srv.load,
                )
                if goback:
                    break

        return any(x.edited for x in self.mgr_srvs)


if __name__ == "__main__":
    parse_write_base_arg()
    curses.wrapper(ConfigAssistantTextSystem)
