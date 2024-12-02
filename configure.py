import curses
import json
import textwrap
from collections import defaultdict
from curses import textpad
from typing import Any, Dict, List, Optional, Set

from musicbot import parse_write_base_arg, write_path
from musicbot.aliases import Aliases
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


class ServerData:
    def __init__(self, guild_id: str, guild_name: Optional[str]) -> None:
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
        return self.path.is_file()

    def __hash__(self) -> int:
        return int(self.id)

    def set(self, option: str, value: Any) -> None:
        self._options[option] = value
        self.edited = True

    def get(self, option: str, default: str) -> Any:
        return self._options.get(option, default)

    def load(self) -> None:
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
        with open(self.path, "w", encoding="utf8") as fh:
            json.dump(self._options, fh)
        self.edited = False


def get_curses_key_const(key: int) -> List[str]:
    c = []
    for a in dir(curses):
        v = getattr(curses, a)
        if isinstance(v, int) and v == key:
            c.append(a)
    return c


def get_text_input(lines: int, cols: int, y: int, x: int) -> str:
    curses.curs_set(1)
    twin = curses.newwin(lines, cols, y, x)
    tpad = textpad.Textbox(twin)
    tpad.stripspaces = False
    t = tpad.edit().strip()
    curses.curs_set(0)
    return t


def config_options(win: curses.window, stdscr: curses.window) -> bool:
    M_PICK_SECTION = 0
    M_PICK_OPTION = 1
    M_EDIT_OPTION = 2

    mgr = Config(write_path(DEFAULT_OPTIONS_FILE))
    sections = mgr.parser.sections()

    edited_options: Set[ConfigOption] = set()
    edit_error_msg = ""
    edit_buffer = ""
    edit_mode = M_PICK_SECTION
    sct_selno = 0
    opt_selno = 0
    opt_viewno = 0

    missing_options: Dict[str, List[str]] = defaultdict(list)
    for mopt in mgr.register.ini_missing_options:
        missing_options[mopt.section].append(mopt.option)

    while True:
        # setup the window for this frame.
        max_y, max_x = win.getmaxyx()
        win.clear()

        # update selected section
        selected_sct: str = sections[sct_selno]

        # Layout window.
        win.hline(2, 0, curses.ACS_HLINE, max_x)
        win.vline(2, 30, curses.ACS_VLINE, max_y)
        win.addch(2, 30, curses.ACS_TTEE)
        if edit_error_msg:
            win.addstr(0, 1, edit_error_msg, curses.color_pair(12))
        else:
            win.addstr(0, 1, "Select a section and option to edit.")
        win.addstr(1, 1, "Section:", curses.A_BOLD)
        win.addstr(1, 10, "[", curses.A_DIM)
        if edit_mode == M_PICK_SECTION:
            win.addstr(1, 11, selected_sct, curses.color_pair(1))
        else:
            win.addstr(1, 11, selected_sct)
        win.addstr(1, 11 + len(selected_sct), "]", curses.A_DIM)

        # Show HUD
        hud = " [F2] Save  [F5] Reload  [ESC] Go Back"
        pad = max_x - len(hud) - 31
        hud += " " * pad
        win.addstr(
            max_y - 1, 31, hud[: max_x - 32], curses.color_pair(1) | curses.A_BOLD
        )

        # build options from the above selected section
        options = mgr.parser.options(selected_sct) + missing_options[selected_sct]
        selected_opt = mgr.register.get_config_option(selected_sct, options[opt_selno])
        opt_viewno = max(0, (opt_selno - (max_y - 3)) + 1)
        visopts = options[opt_viewno : opt_viewno + (max_y - 3)]
        cnf_opt: Optional[ConfigOption] = None
        for i, opt in enumerate(visopts):
            cnf_opt = mgr.register.get_config_option(selected_sct, opt)
            if i + opt_viewno == opt_selno and edit_mode == M_PICK_OPTION:
                flags = curses.color_pair(1)
                # If register returns None, the option does not exist.
                if cnf_opt is None:
                    flags = curses.color_pair(11)
                if cnf_opt in edited_options:
                    flags = curses.color_pair(15)
                # If opt is listed in missing_options, mark it so.
                elif opt in missing_options[selected_sct]:
                    flags = curses.color_pair(13)
                win.addstr(i + 3, 0, f" {opt[:28]} ", flags)
            else:
                flags = 0
                if cnf_opt is None:
                    flags = curses.color_pair(10)
                if cnf_opt in edited_options:
                    flags = curses.color_pair(14)
                elif opt in missing_options[selected_sct]:
                    flags = curses.color_pair(12)
                win.addstr(i + 3, 0, f" {opt[:28]} ", flags)

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
            win.addstr(3, 31, lbl_option, curses.A_BOLD)
            win.addstr(3, 32 + len(lbl_option), selected_opt.option)

            # default value
            dval = mgr.register.to_ini(selected_opt, use_default=True)
            win.addstr(4, 31, lbl_default, curses.A_BOLD)
            win.addstr(4, 32 + len(lbl_default), dval)

            # current setting
            cval = mgr.register.to_ini(selected_opt)
            win.addstr(5, 31, lbl_current, curses.A_BOLD)
            # win.addstr(5, 32 + len(lbl_current), str(vals))
            if selected_opt.option in missing_options[selected_sct]:
                win.addstr(
                    5,
                    33 + len(lbl_current),
                    "This option is missing from your INI file.",
                    curses.color_pair(12),
                )
            win.addstr(6, 33, cval)

            # description
            win.addstr(8, 31, lbl_desc, curses.A_BOLD)
            for i, line in enumerate(comment_lines):
                win.addstr(9 + i, 33, line)

        # display a message for non-existing options.
        else:
            win.addstr(4, 33, "This option is invalid.", curses.A_BOLD)
            win.addstr(5, 33, "It can be removed from your INI file.")

        win.refresh()

        # handle getting the edited string.
        edit_buffer = ""
        if edit_mode == M_EDIT_OPTION:
            if selected_opt is None:
                win.addstr(6, 33, "You cannot edit this option.", curses.color_pair(10))
                edit_mode = M_PICK_OPTION
            else:
                # TODO: Maybe add ConfigOption var for input length.
                edit_buffer = get_text_input(1, 200, 9, 33)
                last_ini_val = mgr.register.to_ini(selected_opt)
                edit_mode = M_PICK_OPTION
                edit_error_msg = ""
                no_error = mgr.update_option(selected_opt, edit_buffer)
                cur_ini_val = mgr.register.to_ini(selected_opt)
                if not no_error or cur_ini_val == last_ini_val:
                    edit_error_msg = (
                        f"The option was not updated: {selected_opt.option}"
                    )
                else:
                    edited_options.add(selected_opt)

        win.refresh()

        # get this frame's key code input, if we didn't just leave edit mode.
        if edit_buffer:
            key = 0
        else:
            key = stdscr.getch()

        # select previous
        if key in KEYS_NAV_PREV:
            edit_error_msg = ""
            if edit_mode == M_PICK_OPTION:
                if opt_selno > 0:
                    opt_selno -= 1
                else:
                    opt_selno = len(options) - 1
            elif edit_mode == M_PICK_SECTION:
                if sct_selno > 0:
                    sct_selno -= 1
                else:
                    sct_selno = len(sections) - 1

        # select next
        elif key in KEYS_NAV_NEXT:
            edit_error_msg = ""
            if edit_mode == M_PICK_OPTION:
                if opt_selno < (len(options) - 1):
                    opt_selno += 1
                else:
                    opt_selno = 0
            elif edit_mode == M_PICK_SECTION:
                if sct_selno < (len(sections) - 1):
                    sct_selno += 1
                else:
                    sct_selno = 0

        # confirm selection
        elif key in KEYS_ENTER:
            edit_error_msg = ""
            # picking aliases
            if edit_mode == M_PICK_SECTION:
                edit_mode = M_PICK_OPTION
                opt_selno = 0
            # picking alias component fields
            elif edit_mode == M_PICK_OPTION:
                edit_mode = M_EDIT_OPTION

        # Reload data
        elif key == curses.KEY_F5:
            mgr = Config(write_path(DEFAULT_OPTIONS_FILE))
            sections = mgr.parser.sections()
            edited_options.clear()
            missing_options.clear()
            for mopt in mgr.register.ini_missing_options:
                missing_options[mopt.section].append(mopt.option)

        # Save data
        elif key == curses.KEY_F2:
            eopts = list(edited_options)
            for eopt in eopts:
                if mgr.save_option(eopt):
                    edited_options.discard(eopt)

        # Go back
        elif key == KEY_ESCAPE:
            if edit_mode == M_PICK_SECTION:
                break
            if edit_mode == M_PICK_OPTION:
                edit_mode = M_PICK_SECTION
                opt_selno = 0

        # handle resize
        elif key == curses.KEY_RESIZE:
            ny, nx = stdscr.getmaxyx()
            curses.resize_term(ny, nx)
            curses.update_lines_cols()
            win.resize(ny - 3, nx)
            stdscr.refresh()
            win.refresh()

    return bool(edited_options)


def config_permissions(win: curses.window, stdscr: curses.window) -> bool:
    mgr = Permissions(write_path(DEFAULT_PERMS_FILE))

    edits_made = False

    return edits_made


def config_aliases(win: curses.window, stdscr: curses.window, mgr: Aliases) -> bool:
    NEW_ENTRY = "[New]"  # pylint: disable=invalid-name

    def get_alias_list(mgr: Aliases) -> List[str]:
        return [NEW_ENTRY] + sorted(mgr.aliases.keys())

    # Constants
    M_PICK_ALIAS = 0  # pylint: disable=invalid-name
    M_PICK_FIELD = 1  # pylint: disable=invalid-name
    M_EDIT_FIELD = 2  # pylint: disable=invalid-name

    # Set up vars and selection list.
    aliases = []
    edits_made = False
    edit_mode = M_PICK_ALIAS
    edit_buffer = ""
    new_alias_name = ""
    alias_selno = 0
    edit_selno = 0
    key = 0

    # run output/update loop.
    while True:
        # setup the window for this frame.
        max_y, max_x = win.getmaxyx()
        win.clear()
        win.vline(0, 14, curses.ACS_VLINE, max_y)
        stdscr.addch(2, 14, curses.ACS_TTEE)

        # Show HUD
        hud = " [F2] Save  [F5] Reload  [ESC] Go Back"
        pad = max_x - len(hud) - 16
        hud += " " * pad
        win.addstr(
            max_y - 1, 15, hud[: max_x - 16], curses.color_pair(1) | curses.A_BOLD
        )

        # build the selection for this "frame"
        aliases = get_alias_list(mgr)
        alias_viewno = max(0, (alias_selno - max_y) + 1)
        visible = aliases[alias_viewno : alias_viewno + max_y]
        selected_alias = ""
        selected_cmd = None
        for i, alias in enumerate(visible):
            flags = 0
            if i + alias_viewno == 0:
                cmd = None
                flags |= curses.A_BOLD
            else:
                cmd = mgr.aliases[alias]

            if alias_selno == i + alias_viewno:
                selected_alias = alias
                selected_cmd = cmd
                flags |= curses.color_pair(1)
                win.addstr(i, 0, f" {alias[:11]} ", flags)
            else:
                win.addstr(i, 0, f" {alias[:11]} ", flags)

        # build info display for selected alias.
        if selected_cmd or edit_mode in [M_PICK_FIELD, M_EDIT_FIELD]:
            # placeholders for edit mode should be one space when empty.
            p_alias = new_alias_name or selected_alias or " "
            p_cmd = " "
            if selected_cmd and selected_cmd[0]:
                p_cmd = selected_cmd[0]
            p_args = " "
            if selected_cmd and selected_cmd[1]:
                p_args = selected_cmd[1]

            # Alias field
            win.addstr(0, 15, "Alias:", curses.A_BOLD)
            if edit_mode == M_PICK_FIELD and edit_selno == 0:
                win.addstr(1, 17, p_alias, curses.color_pair(1))
            else:
                win.addstr(1, 17, p_alias)

            # Command field
            win.addstr(2, 15, "Command:", curses.A_BOLD)
            if edit_mode == M_PICK_FIELD and edit_selno == 1:
                win.addstr(3, 17, p_cmd, curses.color_pair(1))
            else:
                win.addstr(3, 17, p_cmd)

            # Arguments field.
            if (selected_cmd and selected_cmd[1]) or edit_mode:
                win.addstr(4, 15, "Arguments:", curses.A_BOLD)
                if edit_mode == M_PICK_FIELD and edit_selno == 2:
                    win.addstr(5, 17, p_args, curses.color_pair(1))
                else:
                    win.addstr(5, 17, p_args)

        # display a simple message before "New" is edited.
        else:
            edit_selno = 0
            win.addstr(0, 15, "Add a new command alias.")

        win.refresh()

        # handle getting the edited string.
        edit_buffer = ""
        if edit_mode == M_EDIT_FIELD:
            edit_cmd = selected_cmd
            if not edit_cmd:
                edit_cmd = ("", "")

            # edited alias name
            if edit_selno == 0:
                edit_buffer = get_text_input(1, 20, 4, 17)
                if edit_buffer:
                    edits_made = True
                    # save new alias name to buffer and move to command field.
                    if alias_selno == 0:
                        new_alias_name = edit_buffer
                        edit_selno = 1
                    else:
                        # update aliases
                        mgr.remove_alias(selected_alias)
                        mgr.make_alias(edit_buffer, edit_cmd[0], edit_cmd[1])

                        # get the new index value.
                        aliases = get_alias_list(mgr)
                        alias_selno = aliases.index(edit_buffer)
                        edit_mode = M_PICK_FIELD
                else:
                    edit_mode = M_PICK_FIELD

            # edited command name
            elif edit_selno == 1:
                edit_buffer = get_text_input(1, 20, 6, 17)
                if edit_buffer:
                    edits_made = True
                    if new_alias_name:
                        mgr.make_alias(new_alias_name, edit_buffer, "")
                        # get the new index value.
                        aliases = get_alias_list(mgr)
                        alias_selno = aliases.index(new_alias_name)
                        new_alias_name = ""
                    else:
                        mgr.make_alias(selected_alias, edit_buffer, edit_cmd[1])
                edit_mode = M_PICK_FIELD

            # edited arguments field
            elif edit_selno == 2:
                edit_buffer = get_text_input(1, 60, 8, 17)
                edits_made = True
                mgr.make_alias(selected_alias, edit_cmd[0], edit_buffer)
                edit_mode = M_PICK_FIELD

        win.refresh()

        # get this frame's key code input, if we didn't just leave edit mode.
        if edit_buffer:
            key = 0
        else:
            key = stdscr.getch()

        # select previous
        if key in KEYS_NAV_PREV:
            if edit_mode == M_PICK_FIELD:
                if edit_selno > 0:
                    edit_selno -= 1
                else:
                    edit_selno = 2
            elif edit_mode == M_PICK_ALIAS:
                if alias_selno > 0:
                    alias_selno -= 1
                else:
                    alias_selno = len(aliases) - 1

        # select next
        elif key in KEYS_NAV_NEXT:
            if edit_mode == M_PICK_FIELD:
                if edit_selno < 2:
                    edit_selno += 1
                else:
                    edit_selno = 0
            elif edit_mode == M_PICK_ALIAS:
                if alias_selno < (len(aliases) - 1):
                    alias_selno += 1
                else:
                    alias_selno = 0

        # confirm selection
        elif key in KEYS_ENTER:
            # picking aliases
            if edit_mode == M_PICK_ALIAS:
                edit_mode = M_PICK_FIELD
                # new aliases edit name field first.
                if alias_selno == 0:
                    edit_mode = M_EDIT_FIELD
                    edit_selno = 0

            # picking alias component fields
            elif edit_mode == M_PICK_FIELD:
                edit_mode = M_EDIT_FIELD

        # Reload data
        elif key == curses.KEY_F5:
            mgr.load()
            edits_made = False

        # Save data
        elif key == curses.KEY_F2:
            mgr.save()
            edits_made = False

        # Go back
        elif key == KEY_ESCAPE:
            if edit_mode == M_PICK_ALIAS:
                break
            if edit_mode == M_PICK_FIELD:
                edit_mode = M_PICK_ALIAS
                edit_selno = 0

        # handle resize
        elif key == curses.KEY_RESIZE:
            ny, nx = stdscr.getmaxyx()
            curses.resize_term(ny, nx)
            curses.update_lines_cols()
            win.resize(ny - 3, nx)
            stdscr.refresh()
            win.refresh()

    return edits_made


def config_servers(win: curses.window, stdscr: curses.window) -> bool:
    data_path = write_path(DEFAULT_DATA_DIR)
    servers_path = data_path.joinpath(DATA_FILE_SERVERS)
    opt_pattern = "*/"

    M_PICK_SERVER = 0  # pylint: disable=invalid-name
    M_PICK_FIELD = 1  # pylint: disable=invalid-name
    M_EDIT_FIELD = 2  # pylint: disable=invalid-name

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

    servers = get_servers()
    edit_buffer = ""
    edit_selno = 0
    edit_mode = M_PICK_SERVER
    srv_selno = 0
    srv_viewno = 0
    selected_srv = servers[0]
    while True:
        # setup the window for this frame.
        max_y, max_x = win.getmaxyx()
        win.clear()
        # Layout window.
        win.hline(1, 0, curses.ACS_HLINE, max_x)
        win.vline(1, 15, curses.ACS_VLINE, max_y)
        win.addch(1, 15, curses.ACS_TTEE)

        # Show HUD
        hud = " [F2] Save  [F5] Reload  [ESC] Go Back"
        pad = max_x - len(hud) - 16
        hud += " " * pad
        win.addstr(
            max_y - 1, 16, hud[: max_x - 17], curses.color_pair(1) | curses.A_BOLD
        )

        # build the selection for this "frame"
        srv_viewno = max(0, (srv_selno - max_y) + 1)
        visible = servers[srv_viewno : srv_viewno + max_y]
        for i, srv in enumerate(visible):
            flags = 0
            if not srv.has_options:
                flags |= curses.A_DIM
            if i + srv_viewno == srv_selno:
                selected_srv = srv
                flags |= curses.color_pair(1)
                win.addstr(i + 2, 0, f" {srv.name[:12]} ", flags)
            else:
                win.addstr(i + 2, 0, f" {srv.name[:12]} ", flags)

        win.addstr(0, 1, f"Select a server to edit. [ID: {selected_srv.id}]")
        win.refresh()

        # build info display for selected alias.
        # Command Prefix field
        prefix = selected_srv.get("command_prefix", " ")
        win.addstr(2, 16, "Command Prefix:", curses.A_BOLD)
        if edit_mode == M_PICK_FIELD and edit_selno == 0:
            win.addstr(3, 18, prefix, curses.color_pair(1))
        else:
            win.addstr(3, 18, prefix)

        # Playlist field
        playlist = selected_srv.get("auto_playlist", " ")
        win.addstr(4, 16, "Playlist File:", curses.A_BOLD)
        if edit_mode == M_PICK_FIELD and edit_selno == 1:
            win.addstr(5, 18, playlist, curses.color_pair(1))
        else:
            win.addstr(5, 18, playlist)

        # Language field.
        lang = selected_srv.get("language", " ")
        lang = lang or " "
        win.addstr(6, 16, "Language:", curses.A_BOLD)
        if edit_mode == M_PICK_FIELD and edit_selno == 2:
            win.addstr(7, 18, lang, curses.color_pair(1))
        else:
            win.addstr(7, 18, lang)

        win.refresh()

        # handle getting the edited string.
        edit_buffer = ""
        if edit_mode == M_EDIT_FIELD:
            # edited command prefix
            if edit_selno == 0:
                edit_buffer = get_text_input(1, 20, 6, 18)
                selected_srv.set("command_prefix", edit_buffer)
                edit_mode = M_PICK_FIELD

            # edited auto playlist
            elif edit_selno == 1:
                edit_buffer = get_text_input(1, 60, 8, 18)
                if edit_buffer:
                    selected_srv.set("auto_playlist", edit_buffer)
                else:
                    selected_srv.set("auto_playlist", None)
                edit_mode = M_PICK_FIELD

            # edited arguments field
            elif edit_selno == 2:
                edit_buffer = get_text_input(1, 20, 10, 18)
                selected_srv.set("language", edit_buffer)
                edit_mode = M_PICK_FIELD

        # get this frame's key code input, if we didn't just leave edit mode.
        if edit_buffer:
            key = 0
        else:
            key = stdscr.getch()

        # select previous
        if key in KEYS_NAV_PREV:
            if edit_mode == M_PICK_FIELD:
                if edit_selno > 0:
                    edit_selno -= 1
                else:
                    edit_selno = 2
            elif edit_mode == M_PICK_SERVER:
                if srv_selno > 0:
                    srv_selno -= 1
                else:
                    srv_selno = len(servers) - 1

        # select next
        elif key in KEYS_NAV_NEXT:
            if edit_mode == M_PICK_FIELD:
                if edit_selno < 2:
                    edit_selno += 1
                else:
                    edit_selno = 0
            elif edit_mode == M_PICK_SERVER:
                if srv_selno < (len(servers) - 1):
                    srv_selno += 1
                else:
                    srv_selno = 0

        # confirm selection
        elif key in KEYS_ENTER:
            # picking aliases
            if edit_mode == M_PICK_SERVER:
                edit_mode = M_PICK_FIELD
                # new aliases edit name field first.
                if srv_selno == 0:
                    edit_mode = M_EDIT_FIELD
                    edit_selno = 0

            # picking alias component fields
            elif edit_mode == M_PICK_FIELD:
                edit_mode = M_EDIT_FIELD

        # Reload data
        elif key == curses.KEY_F5:
            selected_srv.load()

        # Save data
        elif key == curses.KEY_F2:
            selected_srv.save()

        # Go back
        elif key == KEY_ESCAPE:
            if edit_mode == M_PICK_SERVER:
                break
            if edit_mode == M_PICK_FIELD:
                edit_mode = M_PICK_SERVER
                edit_selno = 0

        # handle resize
        elif key == curses.KEY_RESIZE:
            ny, nx = stdscr.getmaxyx()
            curses.resize_term(ny, nx)
            curses.update_lines_cols()
            win.resize(ny - 3, nx)
            stdscr.refresh()
            win.refresh()

    return any(x.edited for x in servers)


def main(stdscr: curses.window) -> None:
    curses.curs_set(0)  # turn off cursor
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
    alias_mgr = None

    while True:
        max_y, max_x = stdscr.getmaxyx()
        stdscr.clear()
        stdscr.addstr(0, 0, "Select configuration to edit:", curses.A_BOLD)

        # build config selection at top.
        c = 2
        for i, option in enumerate(config_types):
            opt_str = f" {option} "
            if i == config_sel:
                stdscr.addstr(1, c, opt_str, curses.color_pair(1))
            else:
                stdscr.addstr(1, c, opt_str)
            c += len(opt_str)
        stdscr.hline(2, 0, curses.ACS_HLINE, max_x)
        stdscr.addstr(3, 2, config_files[config_types[config_sel]])

        # Get user input
        key = stdscr.getch()
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
            # stdscr.addstr(4, 0, f"You selected: {config_types[config_sel]}")
            selected = True
        elif key == KEY_ESCAPE:
            selected = False
            break

        if selected:
            # enter Options editor
            if config_sel == 0:
                win = curses.newwin(max_y - 3, max_x, 3, 0)
                config_edited[0] = config_options(win, stdscr)
                selected = False

            # enter Permissions editor
            elif config_sel == 1:
                win = curses.newwin(max_y - 3, max_x, 3, 0)
                config_edited[1] = config_permissions(win, stdscr)
                selected = False

            # enter Aliases editor
            elif config_sel == 2:
                win = curses.newwin(max_y - 3, max_x, 3, 0)
                if not alias_mgr:
                    alias_mgr = Aliases(write_path(DEFAULT_COMMAND_ALIAS_FILE), [])
                config_edited[2] = config_aliases(win, stdscr, alias_mgr)
                selected = False

            # enter Server options editor.
            elif config_sel == 3:
                win = curses.newwin(max_y - 3, max_x, 3, 0)
                config_edited[3] = config_servers(win, stdscr)
                selected = False

        stdscr.refresh()


if __name__ == "__main__":
    parse_write_base_arg()
    curses.wrapper(main)
