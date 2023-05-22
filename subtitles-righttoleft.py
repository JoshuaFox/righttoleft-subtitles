import itertools
import os.path
import sys
import time
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, List

import ke

timestamp_kex_str = '[2 #digit] ":" [2 #digit] ":" [2 #digit] "," [3 #digit]'


@dataclass
class Screen:
    instances: ClassVar[int] = 0
    timestamps: str = None
    end_line_found: bool = False
    txt: str = ""
    original_sequence_number: int = -1
    sequence_number: int = -1

    def __post_init__(self):
        Screen.instances += 1
        self.sequence_number = Screen.instances

    def __str__(self):
        return f"""{self.sequence_number}
{self.timestamps}
{self.txt}\n"""


@lru_cache
def punc_ke():
    s = "["
    for c in ";:,.()„“?-—!":
        s += '"' + c + '"|'
    s += "#quote" + "|"
    s += "#double_quote"  # no pipe at end here
    #    s += "#left_brace" + "|" #Rendering of rtl text works correctly when this is NOT moved
    #    s += "#right_brace" # should not occur EOL in rtl text, and if it does, we have worse problems
    s += "]"
    return s


@lru_cache
def rtl_ke():
    s = "["
    for c in range(ord("א"), ord("ת")):
        s += '"' + chr(c) + '"|'
    for c in range(
            ord("\u0600"), ord("\u06FF")
    ):  # Arabic range by unicode because it is not just arranged as alphabet
        s += '"' + chr(c) + '"|'
    s = s[:-1]
    s += "]"

    return s


def normalize(lines):

    lines_stripped = [l.strip().replace("\u2060", "") for l in lines]#strip. remove Word Joiner
    def collapse_blankline_sequences(lines: List[str]):
        groups = (list(group) for _, group in itertools.groupby(lines, lambda x: x))
        return ('' if not group[0] and len(group) > 1 else group[0] for group in groups)
    return collapse_blankline_sequences(lines_stripped)



def move_punc(line):
    assert line == line.strip(), "strip line first" + line
    kexp = "[[1+ " + punc_ke() + "] #end_line]"

    match = ke.search(kexp, line)
    if match:
        assert len(match.regs) == 1
        start, end = match.regs[0]
        assert end == len(line)  # regex finds punc at end of line
        return line[start:] + line[:start]
    else:
        return line


def process(f_in, f_out):
    screen = None
    errors = []
    with open(f_in) as f_i:
        with open(f_out, "w") as file_out:
            lines = f_i.readlines()
            lines_normalized = normalize(lines)
            for line in lines_normalized:
                screen = process_line(line, screen, file_out, errors)
            if screen:  # If there were any lines in the input file at all, don't forget the last one.
                file_out.write(str(screen))
            else:
                raise ValueError("No screens found in file")
    if errors:
        print("Errors\n", "\n".join(errors))


def process_line(line, current_screen,   file_out, errors):
    if line.isdigit():  # nonneg integer
        if current_screen:
            if not current_screen.end_line_found:
                errors.append(f"Blank-line missing:\n{current_screen}")
            file_out.write(str(current_screen))
        current_screen = Screen()
        current_screen.original_sequence_number = int(line)
    elif ke.match(
            '[#timestamp=[' + timestamp_kex_str + '][ #timestamp " --> " #timestamp]]', line
    ):
        if not current_screen: raise ValueError(f"Should reach a sequence number before timestamp {line}")
        current_screen.timestamps = line
    elif ke.search(rtl_ke(), line):

        if not current_screen: raise ValueError(f"Should reach a sequence number before RTL text{line}")

        line_rearranged = move_punc(line)
        current_screen.txt += line_rearranged + "\n"
    elif line == "":
        if not current_screen: raise ValueError(f"Should reach a sequence number before blank line")
        current_screen.end_line_found = True
    else:

        def is_ltr_sentence(line):
            sentence = ke.match(
                "[#punc="
                + punc_ke()
                + " #start_line [1+ [#letter | #digit | #space| #punc]] #end_line]"
                , line)
            sentence_with_letter = ke.match("[1+[#letter ]]", line)
            has_rtl = any((unicodedata.bidirectional(c) == "R") for c in line)
            return sentence and sentence_with_letter and not has_rtl

        if not current_screen: raise ValueError(f"Should reach a sequence number before ordinary text {line}")
        current_screen.txt += line + "\n"
        if not is_ltr_sentence(line):
            raise ValueError(f"expect LTR sentence, found {line}")
    return current_screen


def usage():
    print("Usage: subtitles-righttoleft.py file_in [file_out]")


def main():
    if len(sys.argv) < 2:
        raise ValueError(usage())
    file_in = os.path.abspath(sys.argv[1])
    path_in = Path(file_in)
    if len(sys.argv) > 2:
        file_out = sys.argv[2]
    else:
        file_out = Path(path_in.parent, "rtl_" + path_in.name)
    print("output", file_out)
    process(file_in, file_out)


if __name__ == "__main__":
    start = time.time()
    if sys.argv[1].startswith("-h"):
        usage()
        exit(1)

    main()
    print(round(time.time() - start), "sec")
