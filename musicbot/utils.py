from __future__ import division
from pyparsing import (
    Literal,
    Word,
    Group,
    Forward,
    alphas,
    alphanums,
    Regex,
    ParseException,
    CaselessKeyword,
    Suppress,
    delimitedList,
)
import re
import math
import random
import operator

import sys
import logging
import aiohttp
import inspect

from hashlib import md5
from .constants import DISCORD_MSG_CHAR_LIMIT

log = logging.getLogger(__name__)


def load_file(filename, skip_commented_lines=True, comment_char='#'):
    try:
        with open(filename, encoding='utf8') as f:
            results = []
            for line in f:
                line = line.strip()

                if line and not (skip_commented_lines and line.startswith(comment_char)):
                    results.append(line)

            return results

    except IOError as e:
        print("Error loading", filename, e)
        return []


def write_file(filename, contents):
    with open(filename, 'w', encoding='utf8') as f:
        for item in contents:
            f.write(str(item))
            f.write('\n')

def paginate(content, *, length=DISCORD_MSG_CHAR_LIMIT, reserve=0):
    """
    Split up a large string or list of strings into chunks for sending to discord.
    """
    if type(content) == str:
        contentlist = content.split('\n')
    elif type(content) == list:
        contentlist = content
    else:
        raise ValueError("Content must be str or list, not %s" % type(content))

    chunks = []
    currentchunk = ''

    for line in contentlist:
        if len(currentchunk) + len(line) < length - reserve:
            currentchunk += line + '\n'
        else:
            chunks.append(currentchunk)
            currentchunk = ''

    if currentchunk:
        chunks.append(currentchunk)

    return chunks


async def get_header(session, url, headerfield=None, *, timeout=5):
    req_timeout = aiohttp.ClientTimeout(total = timeout)
    async with session.head(url, timeout = req_timeout) as response:
        if headerfield:
            return response.headers.get(headerfield)
        else:
            return response.headers


def md5sum(filename, limit=0):
    fhash = md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            fhash.update(chunk)
    return fhash.hexdigest()[-limit:]

def fixg(x, dp=2):
    return ('{:.%sf}' % dp).format(x).rstrip('0').rstrip('.')


def ftimedelta(td):
    p1, p2 = str(td).rsplit(':', 1)
    return ':'.join([p1, '{:02d}'.format(int(float(p2)))])


def safe_print(content, *, end='\n', flush=True):
    sys.stdout.buffer.write((content + end).encode('utf-8', 'replace'))
    if flush: sys.stdout.flush()


def avg(i):
    return sum(i) / len(i)


def objdiff(obj1, obj2, *, access_attr=None, depth=0):
    changes = {}

    if access_attr is None:
        attrdir = lambda x: x

    elif access_attr == 'auto':
        if hasattr(obj1, '__slots__') and hasattr(obj2, '__slots__'):
            attrdir = lambda x: getattr(x, '__slots__')

        elif hasattr(obj1, '__dict__') and hasattr(obj2, '__dict__'):
            attrdir = lambda x: getattr(x, '__dict__')

        else:
            # log.everything("{}{} or {} has no slots or dict".format('-' * (depth+1), repr(obj1), repr(obj2)))
            attrdir = dir

    elif isinstance(access_attr, str):
        attrdir = lambda x: list(getattr(x, access_attr))

    else:
        attrdir = dir

    # log.everything("Diffing {o1} and {o2} with {attr}".format(o1=obj1, o2=obj2, attr=access_attr))

    for item in set(attrdir(obj1) + attrdir(obj2)):
        try:
            iobj1 = getattr(obj1, item, AttributeError("No such attr " + item))
            iobj2 = getattr(obj2, item, AttributeError("No such attr " + item))

            # log.everything("Checking {o1}.{attr} and {o2}.{attr}".format(attr=item, o1=repr(obj1), o2=repr(obj2)))

            if depth:
                # log.everything("Inspecting level {}".format(depth))
                idiff = objdiff(iobj1, iobj2, access_attr='auto', depth=depth - 1)
                if idiff:
                    changes[item] = idiff

            elif iobj1 is not iobj2:
                changes[item] = (iobj1, iobj2)
                # log.everything("{1}.{0} ({3}) is not {2}.{0} ({4}) ".format(item, repr(obj1), repr(obj2), iobj1, iobj2))

            else:
                pass
                # log.everything("{obj1}.{item} is {obj2}.{item} ({val1} and {val2})".format(obj1=obj1, obj2=obj2, item=item, val1=iobj1, val2=iobj2))

        except Exception as e:
            # log.everything("Error checking {o1}/{o2}.{item}".format(o1=obj1, o2=obj2, item=item), exc_info=e)
            continue

    return changes

def color_supported():
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

def _func_():
    # emulate __func__ from C++
    return inspect.currentframe().f_back.f_code.co_name

def _get_variable(name):
    stack = inspect.stack()
    try:
        for frames in stack:
            try:
                frame = frames[0]
                current_locals = frame.f_locals
                if name in current_locals:
                    return current_locals[name]
            finally:
                del frame
    finally:
        del stack



class NumericStringParser(object):
    '''
    Most of this code comes from the fourFn.py pyparsing example
    __author__ = 'Paul McGuire'
    __version__ = '$Revision: 0.0 $'
    __date__ = '$Date: 2009-03-20 $'
    __source__ = http://pyparsing.wikispaces.com/file/view/fourFn.py
    http://pyparsing.wikispaces.com/message/view/home/15549426
    
    All I've done is rewrap Paul McGuire's fourFn.py as a class, so I can use it
    more easily in other places.
    '''
    
    class IdentifierException(Exception):
        pass
    
    def push_first(self, strg, loc, toks):
        self.exprStack.append(toks[0])
    
    def push_unary_minus(self, strg, loc, toks):
        for t in toks:
            if t == '-':
                self.exprStack.append('unary -')
            else:
                break
    
    def __init__(self):
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        # use CaselessKeyword for e and pi, to avoid accidentally matching
        # functions that start with 'e' or 'pi' (such as 'exp'); Keyword
        # and CaselessKeyword only match whole words
        e = CaselessKeyword("E")
        pi = CaselessKeyword("PI")
        # fnumber = Combine(Word("+-"+nums, nums) +
        #                    Optional("." + Optional(Word(nums))) +
        #                    Optional(e + Word("+-"+nums, nums)))
        # or use provided pyparsing_common.number, but convert back to str:
        # fnumber = ppc.number().addParseAction(lambda t: str(t[0]))
        fnumber = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
        ident = Word(alphas, alphanums + "_$")

        plus, minus, mult, div, mod = map(Literal, "+-*/%")
        lpar, rpar = map(Suppress, "()")
        addop = plus | minus
        multop = mult | div | mod
        expop = Literal("^")

        expr = Forward()
        expr_list = delimitedList(Group(expr))
        # add parse action that replaces the function identifier with a (name, number of args) tuple
        fn_call = (ident + lpar - Group(expr_list) + rpar).setParseAction(
            lambda t: t.insert(0, (t.pop(0), len(t[0])))
        )
        atom = (
            addop[...]
            + (
                (fn_call | pi | e | fnumber | ident).setParseAction(self.push_first)
                | Group(lpar + expr + rpar)
            )
        ).setParseAction(self.push_unary_minus)

        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left
        # exponents, instead of left-to-right that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor <<= atom + (expop + factor).setParseAction(self.push_first)[...]
        term = factor + (multop + factor).setParseAction(self.push_first)[...]
        expr <<= term + (addop + term).setParseAction(self.push_first)[...]
        self.bnf = expr
        
        # map operator symbols to corresponding arithmetic operations
        self.epsilon = 1e-12
        self.opn = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "^": operator.pow,
            "%": operator.mod,
        }

        self.fn = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "exp": math.exp,
            "abs": abs,
            "int": int,
            "sqrt": math.sqrt,
            "factorial": self.factorial,
            "trunc": lambda a: int(a),
            "round": round,
            "sgn": lambda a: -1 if a < -epsilon else 1 if a > epsilon else 0,
        }
    
    def factorial(self, a):
        return math.factorial(int(a))
    
    def evaluate_stack(self, s):
        op, num_args = s.pop(), 0
        if isinstance(op, tuple):
            op, num_args = op
        if op == "unary -":
            return -self.evaluate_stack(s)
        if op in "+-*/^%":
            # note: operands are pushed onto the stack in reverse order
            op2 = self.evaluate_stack(s)
            op1 = self.evaluate_stack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            # note: args are pushed onto the stack in reverse order
            args = reversed([self.evaluate_stack(s) for _ in range(num_args)])
            return self.fn[op](*args)
        elif op[0].isalpha():
            raise NumericStringParser.IdentifierException(f'invalid identifier \'{op}\'')
        else:
            # try to evaluate as int first, then as float if int fails
            try:
                return int(op)
            except ValueError:
                return float(op)
    
    def eval(self, num_string, parseAll=True):
        # handle decimal numbers without a leading number.
        num_string = re.sub(r'^(\.\d+)', r'0\g<1>', num_string)
        num_string = re.sub(r'([-\+\*\^%/!])(\.\d+)', r'\g<1>0\g<2>', num_string)
        
        # factorial by way of ! is a funny edge case, we handle here with regex.
        num_string = re.sub(r'((?:\d+\.)?\d+)!', r'factorial(\1)', num_string)
        
        self.exprStack = []
        results = self.bnf.parseString(num_string, parseAll)
        val = self.evaluate_stack(self.exprStack[:])
        return val

