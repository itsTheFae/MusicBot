import curses
import pathlib
import time
from curses import panel, textpad

from musicbot import parse_write_base_arg, write_path
from musicbot.aliases import Aliases
from musicbot.bot import MusicBot
from musicbot.config import Config
from musicbot.constants import (
    DEFAULT_COMMAND_ALIAS_FILE,
    DEFAULT_OPTIONS_FILE,
    DEFAULT_PERMS_FILE,
)

KEY_ESCAPE = 27
KEY_FTAB = ord("\t")
KEY_RETURN = ord("\n")
KEYS_NAV_PREV = [curses.KEY_LEFT, curses.KEY_UP, curses.KEY_BTAB]
KEYS_NAV_NEXT = [curses.KEY_RIGHT, curses.KEY_DOWN, KEY_FTAB]
KEYS_ENTER = [KEY_RETURN, curses.KEY_ENTER]


def get_curses_key_const(key: int) -> list[str]:
    c = []
    for a in dir(curses):
        v = getattr(curses, a)
        if isinstance(v, int) and v == key:
            c.append(a)
    return c


def get_text_input(lines, cols, y, x) -> str:
    curses.curs_set(1)
    twin = curses.newwin(lines, cols, y, x)
    tpad = textpad.Textbox(twin)
    tpad.stripspaces = False
    t = tpad.edit().strip()
    curses.curs_set(0)
    return t


def config_aliases(win, stdscr, mgr):
    NEW_ENTRY = "[New]"

    def get_alias_list(mgr) -> list[str]:
        return [NEW_ENTRY] + sorted(mgr.aliases.keys())

    # Constants
    M_PICK_ALIAS = 0
    M_PICK_FIELD = 1
    M_EDIT_FIELD = 2

    # Set up vars and selection list.
    aliases = []
    last_selected_alias = ""
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
        maxY, maxX = win.getmaxyx()
        win.clear()
        win.vline(0, 14, curses.ACS_VLINE, maxY)
        stdscr.addch(2, 14, curses.ACS_TTEE)

        # Show HUD
        hud = " [F2] Save  [F5] Reload  [ESC] Go Back"
        pad = maxX - len(hud) - 16
        hud += " "*pad
        win.addstr(maxY-1, 15, hud[:maxX-16], curses.color_pair(1) | curses.A_BOLD)

        # build the selection for this "frame"
        aliases = get_alias_list(mgr)
        alias_viewno = max(0, (alias_selno - maxY) + 1)
        visible = aliases[alias_viewno:alias_viewno + maxY]
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
            if not selected_cmd:
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

        # Save data
        elif key == curses.KEY_F2:
            mgr.save()
            
        # Go back
        elif key == KEY_ESCAPE:
            if edit_mode == M_PICK_ALIAS:
                break
            elif edit_mode == M_PICK_FIELD:
                edit_mode = M_PICK_ALIAS
                edit_selno = 0

        elif key == curses.KEY_RESIZE:
            nY, nX = stdscr.getmaxyx()
            curses.resize_term(nY, nX)
            curses.update_lines_cols()
            win.resize(nY-3, nX)
            stdscr.refresh()
            win.refresh()

def main(stdscr):
    curses.curs_set(0)  # turn off cursor
    curses.set_escdelay(100)  # set escape delay to 100 ms
    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    # Create a list of config types to manage.
    config_files = {
        "Options": "Manage settings saved in options.ini file.",
        "Permissions": "Manage groups saved in permissions.ini file.",
        "Aliases": "Manage aliases saved in aliases.json file.",
        "Servers": "Manage per-server settings saved in data files.",
    }
    config_types = list(config_files.keys())
    config_sel = 0
    selected = False
    alias_mgr = None

    while True:
        maxY, maxX = stdscr.getmaxyx()
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
        stdscr.hline(2, 0, curses.ACS_HLINE, maxX)
        stdscr.addstr(3, 2, config_files[config_types[config_sel]])

        # Get user input
        key = stdscr.getch()
        if key == curses.KEY_LEFT and config_sel > 0:
            config_sel -= 1
        elif key == curses.KEY_RIGHT and config_sel < len(config_types) - 1:
            config_sel += 1
        elif key == ord("\n") and not selected:
            # stdscr.addstr(4, 0, f"You selected: {config_types[config_sel]}")
            selected = True
        elif key == KEY_ESCAPE:
            selected = False
            break

        if selected and config_sel == 2:
            win = curses.newwin(maxY - 3, maxX, 3, 0)
            if not alias_mgr:
                alias_mgr = Aliases(pathlib.Path(DEFAULT_COMMAND_ALIAS_FILE), [])
            config_aliases(win, stdscr, alias_mgr)
            selected = False

        stdscr.refresh()


if __name__ == "__main__":
    parse_write_base_arg()
    curses.wrapper(main)
