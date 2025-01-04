#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Originally written by Barry Warsaw <barry@python.org>
#
# Minimally patched to make it even more xgettext compatible
# by Peter Funk <pf@artcom-gmbh.de>
#
# 2002-11-22 Jürgen Hermann <jh@web.de>
# Added checks that _() only contains string literals, and
# command line args are resolved to module lists, i.e. you
# can now pass a filename, a module or package name, or a
# directory (including globbing chars, important for Win32).
# Made docstring fit in 80 chars wide displays using pydoc.
#
# 2024-11-07 Fae
# Updated header to match xgettext header.
# Added flags: --package-name, --package-version, --copyright-holder
# Added flag --add-comments for adding comments to translations. Only supports one-line comments.
# Adjusted string extraction to leave escape sequences \N, \U, and \u alone.


# for selftesting
try:
    import fintl

    _ = fintl.gettext
except ImportError:

    def _(msg):
        """Dummy function for i18n testing."""
        return msg


__doc__ = _(
    """pygettext -- Python equivalent of xgettext(1)

Many systems (Solaris, Linux, Gnu) provide extensive tools that ease the
internationalization of C programs. Most of these tools are independent of
the programming language and can be used from within Python programs.
Martin von Loewis' work[1] helps considerably in this regard.

There's one problem though; xgettext is the program that scans source code
looking for message strings, but it groks only C (or C++). Python
introduces a few wrinkles, such as dual quoting characters, triple quoted
strings, and raw strings. xgettext understands none of this.

Enter pygettext, which uses Python's standard tokenize module to scan
Python source code, generating .pot files identical to what GNU xgettext[2]
generates for C and C++ code. From there, the standard GNU tools can be
used.

A word about marking Python strings as candidates for translation. GNU
xgettext recognizes the following keywords: gettext, dgettext, dcgettext,
and gettext_noop. But those can be a lot of text to include all over your
code. C and C++ have a trick: they use the C preprocessor. Most
internationalized C source includes a #define for gettext() to _() so that
what has to be written in the source is much less. Thus these are both
translatable strings:

    gettext("Translatable String")
    _("Translatable String")

Python of course has no preprocessor so this doesn't work so well.  Thus,
pygettext searches only for _() by default, but see the -k/--keyword flag
below for how to augment this.

 [1] https://www.python.org/workshops/1997-10/proceedings/loewis.html
 [2] https://www.gnu.org/software/gettext/gettext.html

NOTE: pygettext attempts to be option and feature compatible with GNU
xgettext where ever possible. However some options are still missing or are
not fully implemented. Also, xgettext's use of command line switches with
option arguments is broken, and in these cases, pygettext just defines
additional switches.

Usage: pygettext [options] inputfile ...

Options:

    -a
    --extract-all
        Extract all strings.

    -d name
    --default-domain=name
        Rename the default output file from messages.pot to name.pot.

    -E
    --escape
        Replace non-ASCII characters with octal escape sequences.

    -D
    --docstrings
        Extract module, class, method, and function docstrings.  These do
        not need to be wrapped in _() markers, and in fact cannot be for
        Python to consider them docstrings. (See also the -X option).

    -h
    --help
        Print this help message and exit.

    -k word
    --keyword=word
        Keywords to look for in addition to the default set, which are:
        %(DEFAULTKEYWORDS)s

        You can have multiple -k flags on the command line.

    -K
    --no-default-keywords
        Disable the default set of keywords (see above).  Any keywords
        explicitly added with the -k/--keyword option are still recognized.

    --no-location
        Do not write filename/lineno location comments.

    -n
    --add-location
        Write filename/lineno location comments indicating where each
        extracted string is found in the source.  These lines appear before
        each msgid.  The style of comments is controlled by the -S/--style
        option.  This is the default.

    -o filename
    --output=filename
        Rename the default output file from messages.pot to filename.  If
        filename is `-' then the output is sent to standard out.

    -p dir
    --output-dir=dir
        Output files will be placed in directory dir.

    -S stylename
    --style stylename
        Specify which style to use for location comments.  Two styles are
        supported:

        Solaris  # File: filename, line: line-number
        GNU      #: filename:line

        The style name is case insensitive.  GNU style is the default.

    -v
    --verbose
        Print the names of the files being processed.

    -V
    --version
        Print the version of pygettext and exit.

    -w columns
    --width=columns
        Set width of output to columns.

    -x filename
    --exclude-file=filename
        Specify a file that contains a list of strings that are not be
        extracted from the input files.  Each string to be excluded must
        appear on a line by itself in the file.

    -X filename
    --no-docstrings=filename
        Specify a file that contains a list of files (one per line) that
        should not have their docstrings extracted.  This is only useful in
        conjunction with the -D option above.

If `inputfile' is -, standard input is read.
"""
)

import ast
import getopt
import glob
import importlib.machinery
import importlib.util
import os
import re
import sys
import time
import token
import tokenize

__version__ = "1.5"

default_keywords = ["_"]
DEFAULTKEYWORDS = ", ".join(default_keywords)

EMPTYSTRING = ""


# The normal pot-file header. msgmerge and Emacs's po-mode work better if it's
# there.
pot_header = _(
    """\
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the %(package_name)s package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: %(package_name)s %(package_version)s\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: %(time)s\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=%(charset)s\\n"
"Content-Transfer-Encoding: %(encoding)s\\n"
"X-Generated-By: pygettext.py %(version)s-mb01\\n"

"""
)
# Matches literal escape sequences so they can be preserved.
pre_escape = re.compile(r"(?<!\\)(\\[NUu](?:[a-fA-F0-9]+|\{[^\}]+\}))")


def usage(code, msg=""):
    """Display some message or the program doc string and exit."""
    print(__doc__ % globals(), file=sys.stderr)
    if msg:
        print(msg, file=sys.stderr)
    sys.exit(code)


def make_escapes(pass_nonascii):
    """Create the escape function association and general escapes."""
    global escapes, escape  # pylint: disable=global-variable-undefined
    if pass_nonascii:
        # Allow non-ascii characters to pass through so that e.g. 'msgid
        # "Höhe"' would result not result in 'msgid "H\366he"'.  Otherwise we
        # escape any character outside the 32..126 range.
        mod = 128
        escape = escape_ascii
    else:
        mod = 256
        escape = escape_nonascii
    escapes = [
        r"\%03o" % i for i in range(mod)  # pylint: disable=consider-using-f-string
    ]
    for i in range(32, 127):
        escapes[i] = chr(i)
    escapes[ord("\\")] = r"\\"
    escapes[ord("\t")] = r"\t"
    escapes[ord("\r")] = r"\r"
    escapes[ord("\n")] = r"\n"
    escapes[ord('"')] = r"\""


def escape_ascii(s, _encoding):
    """escape function used when files are ascii-only."""
    return "".join(escapes[ord(c)] if ord(c) < 128 else c for c in s)


def escape_nonascii(s, encoding):
    """escape function used when files can be non-ascii."""
    return "".join(escapes[b] for b in s.encode(encoding))


def is_literal_string(s):
    """Test string token is a string with a python modifier."""
    return s[0] in "'\"" or (s[0] in "rRuU" and s[1] in "'\"")


def safe_eval(s):
    """Safely normalize strings using eval."""
    # escape literal sequences.
    s = pre_escape.sub(r"\\\1", s)
    # unwrap quotes, safely
    return eval(s, {"__builtins__": {}}, {})  # pylint: disable=eval-used


def normalize(s, encoding):
    """
    This converts the various Python string types into a format that is
    appropriate for .po files, namely much closer to C style.
    """
    lines = s.split("\n")
    if len(lines) == 1:
        s = '"' + escape(s, encoding) + '"'
    else:
        if not lines[-1]:
            del lines[-1]
            lines[-1] = lines[-1] + "\n"
        for i, v in enumerate(lines):
            lines[i] = escape(v, encoding)
        lineterm = '\\n"\n"'
        s = '""\n"' + lineterm.join(lines) + '"'
        b = s.split("\n")
        if len(b) == 2 and b[0] == '""':
            s = s.replace('""\n', "")
    return s


def contains_any(sstr, sset):
    """Check whether 'sstr' contains ANY of the chars in 'sset'"""
    return 1 in [c in sstr for c in sset]


def get_files_for_name(name):
    """Get a list of module files for a filename, a module or package name,
    or a directory.
    """
    if not os.path.exists(name):
        # check for glob chars
        if contains_any(name, "*?[]"):
            files = glob.glob(name)
            flist = []
            for f in files:
                flist.extend(get_files_for_name(f))
            return flist

        # try to find module or package
        try:
            spec = importlib.util.find_spec(name)
            name = spec.origin
        except ImportError:
            name = None
        if not name:
            return []

    if os.path.isdir(name):
        # find all python files in directory
        flist = []
        # get extension for python source files
        _py_ext = importlib.machinery.SOURCE_SUFFIXES[0]
        for root, dirs, files in os.walk(name):
            # don't recurse into CVS directories
            if "CVS" in dirs:
                dirs.remove("CVS")
            # add all *.py files to list
            flist.extend(
                [
                    os.path.join(root, f)
                    for f in files
                    if os.path.splitext(f)[1] == _py_ext
                ]
            )
        return flist

    if os.path.exists(name):
        # a single file
        return [name]

    return []


class TokenEater:
    def __init__(self, options):
        """Token stream processor."""
        self.pyformat = re.compile(r"%(\([a-z0-9_-]+\))?[0-9\.,#+-]*[a-z]+", re.I)
        self.__options = options
        self.__messages = {}
        self.__comments = []
        self.__comment_open = False
        self.__comment_last_line = -1
        self.__state = self.__waiting
        self.__data = []
        self.__lineno = -1
        self.__freshmodule = 1
        self.__curfile = None
        self.__enclosurecount = 0
        self.__last_keyword = ""

    def __call__(self, ttype, tstring, stup, etup, line):
        """Dispatch function for token processing."""
        # print('ttype:', token.tok_name[ttype], 'tstring:', tstring, file=sys.stderr)
        self.__state(ttype, tstring, stup[0])

    def __waiting(self, ttype, tstring, lineno):
        """Process generic token data to extract strings from keywords."""
        opts = self.__options
        self.__commentary(ttype, tstring, lineno)

        # Do docstring extractions, if enabled
        if opts.docstrings and not opts.nodocstrings.get(self.__curfile):
            # module docstring?
            if self.__freshmodule:
                if ttype == tokenize.STRING and is_literal_string(tstring):
                    self.__addentry(safe_eval(tstring), lineno, isdocstring=1)
                    self.__freshmodule = 0
                    return
                if ttype in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING):
                    return
                self.__freshmodule = 0
            # class or func/method docstring?
            if ttype == tokenize.NAME and tstring in ("class", "def"):
                self.__state = self.__suiteseen
                return
        if ttype == tokenize.NAME and tstring in opts.keywords:
            self.__last_keyword = tstring
            self.__state = self.__keywordseen
            return
        if ttype == tokenize.STRING:
            maybe_fstring = ast.parse(tstring, mode="eval").body
            if not isinstance(maybe_fstring, ast.JoinedStr):
                return
            for value in filter(
                lambda node: isinstance(node, ast.FormattedValue), maybe_fstring.values
            ):
                for call in filter(
                    lambda node: isinstance(node, ast.Call), ast.walk(value)
                ):
                    func = call.func
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        func_name = func.attr
                    else:
                        continue

                    if func_name not in opts.keywords:
                        continue
                    if len(call.args) != 1:
                        print(
                            _(
                                "*** %(file)s:%(lineno)s: Seen unexpected amount of"
                                " positional arguments in gettext call: %(source_segment)s"
                            )
                            % {
                                "source_segment": ast.get_source_segment(tstring, call)
                                or tstring,
                                "file": self.__curfile,
                                "lineno": lineno,
                            },
                            file=sys.stderr,
                        )
                        continue
                    if call.keywords:
                        print(
                            _(
                                "*** %(file)s:%(lineno)s: Seen unexpected keyword arguments"
                                " in gettext call: %(source_segment)s"
                            )
                            % {
                                "source_segment": ast.get_source_segment(tstring, call)
                                or tstring,
                                "file": self.__curfile,
                                "lineno": lineno,
                            },
                            file=sys.stderr,
                        )
                        continue
                    arg = call.args[0]
                    if not isinstance(arg, ast.Constant):
                        print(
                            _(
                                "*** %(file)s:%(lineno)s: Seen unexpected argument type"
                                " in gettext call: %(source_segment)s"
                            )
                            % {
                                "source_segment": ast.get_source_segment(tstring, call)
                                or tstring,
                                "file": self.__curfile,
                                "lineno": lineno,
                            },
                            file=sys.stderr,
                        )
                        continue
                    if isinstance(arg.value, str):
                        self.__addentry(arg.value, lineno)

    def __suiteseen(self, ttype, tstring, _lineno):
        """Process container of tokens."""
        # skip over any enclosure pairs until we see the colon
        if ttype == tokenize.OP:
            if tstring == ":" and self.__enclosurecount == 0:
                # we see a colon and we're not in an enclosure: end of def
                self.__state = self.__suitedocstring
            elif tstring in "([{":
                self.__enclosurecount += 1
            elif tstring in ")]}":
                self.__enclosurecount -= 1

    def __suitedocstring(self, ttype, tstring, lineno):
        """Process docstring"""
        # ignore any intervening noise
        if ttype == tokenize.STRING and is_literal_string(tstring):
            self.__addentry(safe_eval(tstring), lineno, isdocstring=1)
            self.__state = self.__waiting
        elif ttype not in (tokenize.NEWLINE, tokenize.INDENT, tokenize.COMMENT):
            # there was no class docstring
            self.__state = self.__waiting

    def __keywordseen(self, ttype, tstring, _lineno):
        """Reset keyword data."""
        if ttype == tokenize.OP and tstring == "(":
            self.__data = []
            self.__state = self.__openseen
        else:
            self.__state = self.__waiting

    def __openseen(self, ttype, tstring, lineno):
        """Process strings inside a keyword."""
        self.__commentary(ttype, tstring, lineno)

        if ttype == tokenize.OP and tstring in (")", ","):
            # We've seen the last of the translatable strings.  Record the
            # line number of the first line of the strings and update the list
            # of messages seen.  Reset state for the next batch.  If there
            # were no strings inside _(), then just ignore this entry.
            if self.__data:
                self.__addentry(EMPTYSTRING.join(self.__data))
            self.__state = self.__waiting
        elif ttype == tokenize.STRING and is_literal_string(tstring):
            if self.__lineno == -1:
                self.__lineno = lineno
            self.__data.append(safe_eval(tstring))
        elif ttype not in [
            tokenize.COMMENT,
            token.INDENT,
            token.DEDENT,
            token.NEWLINE,
            tokenize.NL,
        ]:
            # warn if we see anything else than STRING or whitespace
            """# hopefully not an issue. :)
            print(_(
                '*** %(file)s:%(lineno)s: Seen unexpected token "%(token)s"'
                ) % {
                'token': tstring,
                'file': self.__curfile,
                'lineno': lineno
                }, file=sys.stderr)
            #"""
            self.__state = self.__waiting

    def __commentary(self, ttype, tstring, lineno):
        """Process comment data."""
        opts = self.__options
        if self.__comment_open and ttype not in (tokenize.COMMENT, tokenize.NL):
            self.__comment_open = False

        if ttype == tokenize.COMMENT and tstring:
            comment_text = tstring.lstrip("#").strip()
            if any(comment_text.startswith(tag) for tag in opts.comment_tags):
                self.__comment_open = True
                self.__comment_last_line = lineno
                self.__comments.append(comment_text)
                return
            if self.__comment_open:
                self.__comments.append(comment_text)

        ll = self.__comment_last_line
        if ll > 0 and ll + 2 < lineno:
            self.__comments = []
            self.__comment_open = False
            self.__comment_last_line = -1

    def __addentry(self, msg, lineno=None, isdocstring=0):
        """Adds a new message entry."""
        if lineno is None:
            lineno = self.__lineno
            self.__lineno = -1
        if msg not in self.__options.toexclude:
            usedby = f"Used by: {self.__last_keyword}"
            if not self.has_comment(msg, usedby):
                self.__comments.append(usedby)
            entry = (self.__curfile, lineno)
            self.__messages.setdefault(msg, {})[entry] = (isdocstring, self.__comments)
            self.__comments = []

    def has_comment(self, msg, comment):
        """Check if an entry has the given comment."""
        if msg not in self.__messages:
            return False
        for k, v in self.__messages[msg].items():
            if comment in v[1]:
                return True
        return False

    def set_filename(self, filename):
        """Update file name and signal fresh module."""
        self.__curfile = filename
        self.__freshmodule = 1

    def write(self, fp):
        """
        Write the message data into the POT file.
        """
        options = self.__options
        timestamp = time.strftime("%Y-%m-%d %H:%M%z")
        encoding = fp.encoding if fp.encoding else "UTF-8"
        print(
            pot_header
            % {
                "time": timestamp,
                "version": __version__,
                "charset": encoding,
                "package_name": options.package_name,
                "package_version": options.package_version,
                "copyright-holder": options.copyright_holder,
                "encoding": "8bit",
            },
            file=fp,
        )
        # Sort the entries.  First sort each particular entry's keys, then
        # sort all the entries by their first item.
        reverse = {}
        for k, v in self.__messages.items():
            keys = sorted(v.keys())
            reverse.setdefault(tuple(keys), []).append((k, v))
        rkeys = sorted(reverse.keys())
        for rkey in rkeys:
            rentries = reverse[rkey]
            rentries.sort()
            for k, v in rentries:
                # If the entry was gleaned out of a docstring, then add a
                # comment stating so.  This is to aid translators who may wish
                # to skip translating some unimportant docstrings.
                isdocstring = any(x[0] for x in v.values())
                comments = []
                for x in v.values():
                    comments += x[1]
                # k is the message string, v is a dictionary-set of (filename,
                # lineno) tuples.  We want to sort the entries in v first by
                # file name and then by line number.
                v = sorted(v.keys())
                if not options.writelocations:
                    pass
                # location comments are different b/w Solaris and GNU:
                elif options.locationstyle == options.SOLARIS:
                    for filename, lineno in v:
                        d = {"filename": filename, "lineno": lineno}
                        print(_("# File: %(filename)s, line: %(lineno)d") % d, file=fp)
                elif options.locationstyle == options.GNU:
                    # insert comments if any.
                    for c in comments:
                        if c:
                            print(f"#. {c}", file=fp)

                    # fit as many locations on one line, as long as the
                    # resulting line length doesn't exceed 'options.width'
                    locline = "#:"
                    for filename, lineno in v:
                        d = {"filename": filename, "lineno": lineno}
                        s = _(" %(filename)s:%(lineno)d") % d
                        if len(locline) + len(s) <= options.width:
                            locline = locline + s
                        else:
                            print(locline, file=fp)
                            locline = "#:" + s
                    if len(locline) > 2:
                        print(locline, file=fp)

                flags = []
                if isdocstring:
                    flags.append("python-docstring")
                if self.pyformat.search(k) is not None and not isdocstring:
                    flags.append("python-format")
                

                if flags:
                    print(f"#, {','.join(flags)}", file=fp)
                print("msgid", normalize(k, encoding), file=fp)
                print('msgstr ""\n', file=fp)


def main():
    """
    pygettext program entry point.
    """
    global default_keywords  # pylint: disable=global-statement
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "ad:DEhk:Kno:p:S:Vvw:x:X:",
            [
                "extract-all",
                "default-domain=",
                "escape",
                "help",
                "keyword=",
                "no-default-keywords",
                "add-location",
                "no-location",
                "output=",
                "output-dir=",
                "style=",
                "verbose",
                "version",
                "width=",
                "exclude-file=",
                "docstrings",
                "no-docstrings",
                "package-name=",
                "package-version=",
                "copyright-holder=",
                "add-comments=",
            ],
        )
    except getopt.error as msg:
        usage(1, msg)

    # for holding option values
    class Options:
        # constants
        GNU = 1
        SOLARIS = 2
        # defaults
        extractall = 0  # FIXME: currently this option has no effect at all.
        escape = 0
        keywords = []
        outpath = ""
        outfile = "messages.pot"
        writelocations = 1
        locationstyle = GNU
        verbose = 0
        width = 78
        excludefilename = ""
        docstrings = 0
        nodocstrings = {}
        package_name = "PACKAGE NAME"
        package_version = "PACKAGE VERSION"
        copyright_holder = "THE PACKAGE'S COPYRIGHT HOLDER"
        comment_tags = []
        toexclude = []

    options = Options()
    locations = {
        "gnu": options.GNU,
        "solaris": options.SOLARIS,
    }

    # parse options
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(0)
        elif opt in ("-a", "--extract-all"):
            options.extractall = 1
        elif opt in ("-d", "--default-domain"):
            options.outfile = arg + ".pot"
        elif opt in ("-E", "--escape"):
            options.escape = 1
        elif opt in ("-D", "--docstrings"):
            options.docstrings = 1
        elif opt in ("-k", "--keyword"):
            options.keywords.append(arg)
        elif opt in ("-K", "--no-default-keywords"):
            default_keywords = []
        elif opt in ("-n", "--add-location"):
            options.writelocations = 1
        elif opt in ("--no-location",):
            options.writelocations = 0
        elif opt in ("-S", "--style"):
            options.locationstyle = locations.get(arg.lower())
            if options.locationstyle is None:
                usage(1, _("Invalid value for --style: %s") % arg)
        elif opt in ("-o", "--output"):
            options.outfile = arg
        elif opt in ("-p", "--output-dir"):
            options.outpath = arg
        elif opt in ("-v", "--verbose"):
            options.verbose = 1
        elif opt in ("-V", "--version"):
            print(_("pygettext.py (xgettext for Python) %s") % __version__)
            sys.exit(0)
        elif opt in ("-w", "--width"):
            try:
                options.width = int(arg)
            except ValueError:
                usage(1, _("--width argument must be an integer: %s") % arg)
        elif opt in ("-x", "--exclude-file"):
            options.excludefilename = arg
        elif opt in ("-X", "--no-docstrings"):
            with open(arg, encoding="UTF-8") as fp:
                while 1:
                    line = fp.readline()
                    if not line:
                        break
                    options.nodocstrings[line[:-1]] = 1
        elif opt in ("--package-name"):
            options.package_name = arg
        elif opt in ("--package-version"):
            options.package_version = arg
        elif opt in ("--copyright-holder"):
            options.copyright_holder = arg
        elif opt in ("--add-comments"):
            options.comment_tags.append(arg)
            print(f"comment: '{arg}'")

    # calculate escapes
    make_escapes(not options.escape)

    # calculate all keywords
    options.keywords.extend(default_keywords)

    # initialize list of strings to exclude
    if options.excludefilename:
        try:
            with open(options.excludefilename, encoding="UTF-8") as fp:
                options.toexclude = fp.readlines()
        except IOError:
            print(
                _("Can't read --exclude-file: %s") % options.excludefilename,
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        options.toexclude = []

    # resolve args to module lists
    expanded = []
    for arg in args:
        if arg == "-":
            expanded.append(arg)
        else:
            expanded.extend(get_files_for_name(arg))
    args = expanded

    # slurp through all the files
    eater = TokenEater(options)
    for filename in args:
        if filename == "-":
            if options.verbose:
                print(_("Reading standard input"))
            fp = sys.stdin.buffer
            closep = 0
        else:
            if options.verbose:
                print(_("Working on %s") % filename)
            fp = open(filename, "rb")  # pylint: disable=consider-using-with
            closep = 1
        try:
            eater.set_filename(filename)
            try:
                tokens = tokenize.tokenize(fp.readline)
                for _token in tokens:
                    eater(*_token)
            except tokenize.TokenError as e:
                print(
                    "%s: %s, line %d, column %d"  # pylint: disable=C0209
                    % (e.args[0], filename, e.args[1][0], e.args[1][1]),
                    file=sys.stderr,
                )
        finally:
            if closep:
                fp.close()

    # write the output
    if options.outfile == "-":
        fp = sys.stdout
        closep = 0
    else:
        if options.outpath:
            options.outfile = os.path.join(options.outpath, options.outfile)
        fp = open(  # pylint: disable=consider-using-with
            options.outfile, "w", encoding="UTF-8"
        )
        closep = 1
    try:
        eater.write(fp)
    finally:
        if closep:
            fp.close()


if __name__ == "__main__":
    main()
    # some more test strings
    # this one creates a warning
    _(  # pylint: disable=expression-not-assigned
        '*** Seen unexpected token "%(token)s"'
    ) % {"token": "test"}
    _("more" "than" "one" "string")  # pylint: disable=implicit-str-concat
