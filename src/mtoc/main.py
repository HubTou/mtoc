#!/usr/bin/env python
""" mtoc - show Manual table of contents
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import getopt
import gzip
import logging
import os
import re
import shlex
import sys

# Version string used by the what(1) and ident(1) commands:
ID = "@(#) $Id: mtoc - show Manual table of contents v1.1.0 (July 20, 2021) by Hubert Tournier $"

# Default parameters. Can be overcome by environment variables, then command line options
parameters = {
    "No man pages": False,
    "No mdoc pages": False,
    "Interpret Dq": False,
    "Interpret Pa": "",
    "Interpret Xr": False,
    "Files" : [],
    "Print type" : False,
}


################################################################################
def display_help():
    """Displays usage and help"""
    print("usage: mtoc [--debug] [--help|-?] [--version]", file=sys.stderr)
    print("       [-f|--file|--whatis FILE] [-n|--no MACROS] [-t|--type]", file=sys.stderr)
    print("       [--Dq] [--Pa|--PaSq] [--PaDq] [--Xr]", file=sys.stderr)
    print("       [--] [SECTION ...]", file=sys.stderr)
    print(
        "  -----------------------  ----------------------------------------------------",
        file=sys.stderr
    )
    print(
        "  -f|--file|--whatis FILE  Process a specific file, like whatis(1) [*]",
        file=sys.stderr
    )
    print("  -n|--no MACROS           Discard man or mdoc macros [*]", file=sys.stderr)
    print("  -t|--type                Print type of man page (ie. man, mdoc, other, so)", file=sys.stderr)
    print("  --Dq                     Interpret .Dq (double quotes) macros", file=sys.stderr)
    print(
        "  --Pa|--PaSq              Interpret .Pa (path) macros as single quoted strings",
        file=sys.stderr
    )
    print(
        "  --PaDq                   Interpret .Pa (path) macros as double quoted strings",
        file=sys.stderr
    )
    print("  --Xr                     Interpret .Xr (cross reference) macros", file=sys.stderr)
    print("  --debug                  Enable debug mode", file=sys.stderr)
    print("  --help|-?                Print usage and this help message and exit", file=sys.stderr)
    print("  --version                Print version and exit", file=sys.stderr)
    print("  --                       Options processing terminator", file=sys.stderr)
    print("  [SECTION ...]            The Manual section(s) you want to list", file=sys.stderr)
    print(file=sys.stderr)
    print("  [*] These options can be used multiple times", file=sys.stderr)
    print(file=sys.stderr)


################################################################################
def process_environment_variables():
    """Process environment variables"""

    if "MTOC_DEBUG" in os.environ.keys():
        logging.disable(logging.NOTSET)


################################################################################
def process_command_line():
    """Process command line options"""
    # pylint: disable=C0103
    global parameters
    # pylint: enable=C0103

    # option letters followed by : expect an argument
    # same for option strings followed by =
    character_options = "f:n:t?"
    string_options = [
        "debug",
        "file=",
        "help",
        "no=",
        "type",
        "version",
        "Dq",
        "Pa",
        "PaSq",
        "PaDq",
        "whatis=",
        "Xr",
    ]

    try:
        options, remaining_arguments = getopt.getopt(
            sys.argv[1:], character_options, string_options
        )
    except getopt.GetoptError as error:
        logging.critical("Syntax error: %s", error)
        display_help()
        sys.exit(1)

    for option, parameter in options:

        if option == "--Dq":
            parameters["Interpret Dq"] = True

        elif option in ("--Pa", "--PaSq"):
            parameters["Interpret Pa"] = "'"

        elif option == "--PaDq":
            parameters["Interpret Pa"] = '"'

        elif option == "--Xr":
            parameters["Interpret Xr"] = True

        elif option in ("-n", "--no"):
            if parameter.lower() == "man":
                parameters["No man pages"] = True
            elif parameter.lower() == "mdoc":
                parameters["No mdoc pages"] = True
            else:
                logging.critical('The -n|--no option only accepts "man" or "mdoc" as parameter')
                sys.exit(1)

        elif option in ("-f", "--file", "--whatis"):
            if os.path.isfile(parameter):
                parameters["Files"].append(parameter)
            else:
                logging.critical('The "%s" file does not exist!', parameter)
                sys.exit(1)

        elif option in ("-t", "--type"):
            parameters["Print type"] = True

        elif option == "--debug":
            logging.disable(logging.NOTSET)

        elif option in ("--help", "-?"):
            display_help()
            sys.exit(0)

        elif option == "--version":
            print(ID.replace("@(" + "#)" + " $" + "Id" + ": ", "").replace(" $", ""))
            sys.exit(0)

    logging.debug("process_command_line(): parameters:")
    logging.debug(parameters)
    logging.debug("process_command_line(): remaining_arguments:")
    logging.debug(remaining_arguments)

    return remaining_arguments


################################################################################
def show_manual_sections():
    """Show the sections of the Manual"""
    print("Sections of the manual:")
    print("=======================")
    print("1. General Commands Manual")
    print("2. System Calls Manual")
    print("3. Library Functions Manual")
    print("4. Kernel Interfaces Manual")
    print("5. File Formats Manual")
    print("6. Games Manual")
    print("7. Miscellaneous Information Manual")
    print("8. System Manager's Manual")
    print("9. Kernel Developer's Manual")
    print("--")
    print("Provide a section number as a parameter to see its table of contents.")


################################################################################
def strip_roff_comments(text):
    """Remove *roff(7) comments in the input text"""

    # Request lines with only a control character and optional trailing
    # whitespace are stripped from input:
    text = re.sub(r"^\.[ 	]*$", "", text)

    # A request line beginning with a control character and comment escape '.\"'
    # is also ignored:
    text = re.sub(r'^\.\\".*', "", text)

    # Text following an escaped double-quote '\"', whether in a request, macro,
    # or text line, is ignored to the end of the line:
    text = re.sub(r'\\".*', "", text)

    # The '\#' GNU troff(1) extension does the same:
    text = re.sub(r"\\#.*", "", text)

    return text


################################################################################
def strip_roff_font_style_macros(text):
    """Remove *roff(7) font style macros in the input text"""

    return re.sub(r"^\.(B|BI|BR|CB|CI|CR|CW|I|IB|IR|LG|NL|P|R|RB|RI|SB|SM) +", "", text)


################################################################################
def replace_roff_special_characters(text):
    """Replace some *roff(7) special characters in the input text"""

    if "\\" in text:
        # See https://www.freebsd.org/cgi/man.cgi?query=mandoc_char for a complete list
        text = re.sub(r"\\&", "", text)
        text = re.sub(r"\\\.", ".", text)
        text = re.sub(r"\\-", "-", text)
        text = re.sub(r"\\\(aq", "'", text)
        text = re.sub(r"\\\(em", "", text)
        text = re.sub(r"\\\(tm", "tm", text)
        text = re.sub(r"\\\([lr]q", '"', text)
        text = re.sub(r"\\\[rg\]", "(R)", text)

        # Don't process user defined strings (\*) beside the font style ones:
        text = re.sub(r"\\f\\\*\[[^\]]*\]", "", text)
        text = re.sub(r"\\f[^\*]", "", text)

        # End of line backslash:
        text = re.sub(r" *\\$", "", text)

        # "\ " is not processed as it may still be useful

    return text


################################################################################
def replace_roff_user_defined_strings(text, user_defined_strings):
    """Replace *roff(7) user defined strings in the input text"""

    if "\\*" not in text:
        return text

    new_text = ""
    slash = False
    star = False
    in_short_key = False
    in_long_key = False
    key = ""

    for character in text:
        if character == "\\":
            slash = True
        elif slash:
            slash = False
            if character == "*":
                star = True
            else:
                new_text += character
        elif star:
            star = False
            if character == "(":
                in_short_key = True
            elif character == "[":
                in_long_key = True
            else:
                if character in user_defined_strings.keys():
                    new_text += user_defined_strings[character]
                elif character == "R":
                    new_text += "(Reg.)"
                elif character == "S":
                    pass
                else:
                    logging.debug("UNDEFINED user defined string: %s", character)
        elif in_short_key:
            key += character
            if len(key) == 2:
                in_short_key = False
                if key in user_defined_strings.keys():
                    new_text += user_defined_strings[key]
                elif key in ("lq", "rq"):
                    new_text += '"'
                elif key == "Tm":
                    new_text += "(TM)"
                else:
                    logging.debug("UNDEFINED user defined string: %s", key)
        elif in_long_key:
            if character == "]":
                in_long_key = False
                if key in user_defined_strings.keys():
                    new_text += user_defined_strings[key]
                else:
                    logging.debug("UNDEFINED user defined string: %s", key)
            else:
                key += character
        else:
            new_text += character

    return new_text


################################################################################
def whatis(filename, section, basename, nb_of_so_redirections):
    """Show the entry name and its one line description, whatis(1) like"""
    logging.debug("mtoc.whatis(%s):", filename)

    file_content = None
    if filename.endswith(".gz"):
        with gzip.open(filename, "rb") as file:
            file_content = file.readlines()
    else:
        with open(filename, "rb") as file:
            file_content = file.readlines()

    in_mandoc_section_name = False
    in_mdoc_section_name = False
    in_multi_line_macro = False
    in_description = False
    whatis_text = ""
    items = [ basename ]
    defined_strings = {}
    for line in file_content:
        text_line = line.decode("utf-8", "replace").rstrip()
        text_line = strip_roff_comments(text_line)

        if text_line:
            if in_mandoc_section_name:
                if not text_line.startswith(".SH"):
                    logging.debug(text_line)

                text_line = strip_roff_font_style_macros(text_line)
                text_line = replace_roff_special_characters(text_line)
                text_line = replace_roff_user_defined_strings(text_line, defined_strings)

                # Kludge for groff_hdtbl(7) or I should support if/ie macros:
                text_line = text_line.replace('\\..', "")

                text_line = text_line.replace("\\\\", "\\")
                text_line = re.sub(r"\\ ", " ", text_line)
                text_line = re.sub(r"[ 	]+", " ", text_line)
                text_line = re.sub(r"-+", "-", text_line)

                # .SH NAME section end macro line:
                if text_line.startswith(".SH") or text_line.startswith(".SS"):
                    items.sort()
                    if whatis_text.startswith("("):
                        whatis_text = ", ".join(items) + whatis_text
                    else:
                        # Print the section number if no one line description is provided:
                        whatis_text = ", ".join(items) + "(" + section + ") - " + whatis_text
                    break

                # .ig or .de multi lines macros handling (see groff_out(5)) :
                if text_line.startswith(".ig") or text_line.startswith(".de"):
                    in_multi_line_macro = True
                    continue
                if in_multi_line_macro:
                    if text_line.startswith(".."):
                        in_multi_line_macro = False
                    continue

                # Skip other macros
                if text_line.startswith("."):
                    continue

                if not in_description:
                    if text_line.startswith("-"):
                        in_description = True
                        whatis_text = "(" + section + ") " + text_line
                        text_line = ""

                    elif " - " in text_line:
                        in_description = True
                        description = re.sub(r".* - ", "", text_line)
                        whatis_text = re.sub(r" - ", "(" + section + ") - ", description, count=1)

                        text_line = re.sub(r" - .*", "", text_line)

                    if text_line:
                        if "," not in text_line:
                            if text_line not in items:
                                items.append(text_line)
                        else:
                            for man_item in text_line.replace(" ", "").split(","):
                                if man_item and man_item not in items:
                                    items.append(man_item)

                elif text_line:
                    whatis_text += " " + text_line

            elif in_mdoc_section_name:
                if not text_line.startswith(".Sh"):
                    logging.debug(text_line)

                text_line = strip_roff_font_style_macros(text_line)
                text_line = replace_roff_special_characters(text_line)
                text_line = replace_roff_user_defined_strings(text_line, defined_strings)
                text_line = text_line.replace("\\\\", "\\")
                text_line = re.sub(r"\\ ", " ", text_line)
                text_line = re.sub(r"[ 	]+", " ", text_line)
                text_line = re.sub(r"-+", "-", text_line)

                # .Nm (manual name) macro line handling:
                # - there may be several of them
                # - the first ones should end with a comma for multi-commands man pages
                # - may contain space+comma separation on the same line
                # - may be enclosed in double quotes if they contain a white space
                # - the filename is always mentioned, even if absent from the manual page file
                if text_line.startswith(".Nm"):
                    text_line = re.sub(r"^\.Nm ", "", text_line)
                    text_line = re.sub(r" *,? *$", "", text_line)
                    text_line = re.sub(r" *,", ",", text_line)
                    text_line = re.sub(r'"', "", text_line)
                    if "," not in text_line:
                        if text_line not in items:
                            items.append(text_line)
                    else:
                        for man_item in text_line.replace(" ", "").split(","):
                            if man_item and man_item not in items:
                                items.append(man_item)

                # .Nd (one-line manual description) macro line handling:
                # - may be alone on its line
                # - may span on more than one line
                # - may be enclosed in double quotes
                elif text_line.startswith(".Nd"):
                    text_line = re.sub(r"^\.Nd *\"?", "", text_line)
                    text_line = re.sub(r"\"? *$", "", text_line)
                    if text_line:
                        whatis_text += "(" + section + ") - " + text_line
                    else:
                        whatis_text += "(" + section + ") -"

                # .Sh NAME section end macro line:
                elif text_line.startswith(".Sh") or text_line.startswith(".Ss"):
                    items.sort()
                    whatis_text = ", ".join(items) + whatis_text
                    break

                # Operating Systems macro lines handling:
                elif text_line.startswith(".Ux"):
                    whatis_text += " UNIX"
                elif text_line.startswith(".At"):
                    text_line = re.sub(r"^\.At *", "", text_line)
                    if not text_line:
                        whatis_text += " AT&T UNIX"
                    elif text_line.startswith("v"):
                        text_line = re.sub(r"^v", "Version ", text_line)
                        whatis_text += " " + text_line + " AT&T UNIX"
                    elif text_line.startswith("32v"):
                        whatis_text += " Version 32V AT&T UNIX"
                    elif text_line.startswith("III"):
                        whatis_text += " AT&T System III UNIX"
                    elif text_line.startswith("V."):
                        text_line = re.sub(r"^V\.", "AT&T System V Release ", text_line)
                        whatis_text += " " + text_line + " UNIX"
                    elif text_line.startswith("V"):
                        whatis_text += " AT&T System V UNIX"
                elif text_line.startswith(".Bx"):
                    text_line = re.sub(r"^\.Bx *", "", text_line)
                    text_line = re.sub(r"-alpha", " (currently in alpha test)", text_line)
                    text_line = re.sub(r"-beta", " (currently in beta test)", text_line)
                    text_line = re.sub(r"-devel", " (currently under development)", text_line)
                    if not text_line:
                        whatis_text += " BSD"
                    elif re.match(r"4\.3 ([Tt]ahoe|[Rr]eno)", text_line):
                        text_line = re.sub(r" ", "  ", text_line)
                        whatis_text += " " + text_line + "BSD"
                    elif re.match(r"4\.4 [Ll]ite2?", text_line):
                        text_line = re.sub(r"4\.4 [Ll]ite", "4.4BSD-Lite", text_line)
                        whatis_text += " " + text_line
                    else:
                        whatis_text += " " + text_line + "BSD"
                elif text_line.startswith(".Bsx"):
                    text_line = re.sub(r"^\.Bsx", "BSD/OS", text_line)
                    whatis_text += " " + text_line
                elif text_line.startswith(".Nx"):
                    text_line = re.sub(r"^\.Nx", "NetBSD", text_line)
                    whatis_text += " " + text_line
                elif text_line.startswith(".Fx"):
                    text_line = re.sub(r"^\.Fx", "FreeBSD", text_line)
                    whatis_text += " " + text_line
                elif text_line.startswith(".Ox"):
                    text_line = re.sub(r"^\.Ox", "OpenBSD", text_line)
                    whatis_text += " " + text_line
                elif text_line.startswith(".Dx"):
                    text_line = re.sub(r"^\.Dx", "DragonFly", text_line)
                    whatis_text += " " + text_line

                # .Dq TEXT macro line handling:
                # - the TEXT is sometimes already double quoted (ie. big(5))
                elif text_line.startswith(".Dq"):
                    if parameters["Interpret Dq"]:
                        text_line = re.sub(r"^\.Dq ", '"', text_line)
                        text_line = re.sub(r" *$", '"', text_line)
                        text_line = re.sub(r'""', '"', text_line)
                    else:
                        text_line = re.sub(r"^\.Dq ", "", text_line)
                    whatis_text += " " + text_line

                # .Pa PATH macro line handling:
                elif text_line.startswith(".Pa"):
                    text_line = re.sub(r"^\.Pa ", parameters["Interpret Pa"], text_line)
                    text_line = re.sub(r" *$", parameters["Interpret Pa"], text_line)
                    whatis_text += " " + text_line

                # .Xr MAN_ITEM MAN_SECTION macro line handling:
                elif text_line.startswith(".Xr"):
                    text_line = re.sub(r"^\.Xr ", "", text_line)
                    if parameters["Interpret Xr"]:
                        text_line = re.sub(r" ", "(", text_line, count=1)
                        text_line = re.sub(r" *$", ")", text_line)
                    whatis_text += " " + text_line

                # Skip other macros
                elif text_line.startswith("."):
                    continue

                # .Nd (one-line manual description) continuation text line handling:
                # - may start with a .Xx macro
                # - may be enclosed in double quotes
                elif text_line.strip():
                    text_line = re.sub(r"^\.[A-Za-z]+ \"?", "", text_line)
                    text_line = re.sub(r"\"? *$", "", text_line)
                    whatis_text += " " + text_line

        if (text_line.startswith(".SH NAME") or text_line.startswith('.SH "NAME"')) \
        and not parameters["No man pages"]:
            logging.debug(text_line)
            in_mandoc_section_name = True

        elif text_line.startswith(".Sh NAME") \
        and not parameters["No mdoc pages"]:
            logging.debug(text_line)
            in_mdoc_section_name = True

        elif text_line.startswith(".TH") \
        or text_line.startswith(".Dt"):
            logging.debug(text_line)
            text_line = replace_roff_user_defined_strings(text_line, defined_strings)
            text_line = text_line.lower()
            text_line = replace_roff_special_characters(text_line)
            text_line = text_line.replace("\\\\_", "_")

            other_name = shlex.split(text_line)[1]
            other_name = re.sub(r'"', "", other_name)
            if other_name not in items:
                items.append(other_name)

            other_section = shlex.split(text_line)[2]
            other_section = re.sub(r'"', "", other_section)
            if other_section != section:
                if other_section < section:
                    section = other_section + ", " + section
                else:
                    section = section + ", " + other_section

        elif text_line.startswith(".SO") or text_line.startswith(".so"):
            logging.debug(text_line)
            # Follow non standard Groff SOurce redirection:
            for directory in get_manpath_directories():
                new_filename = directory + os.sep + text_line.split()[1]
                new_section = re.sub(r"^.*\.", "", new_filename)
                if not new_filename.endswith(".gz"):
                    new_filename += ".gz"
                if os.path.isfile(new_filename):
                    if nb_of_so_redirections == 3:
                        logging.critical("Too many .so source file redirections")
                        sys.exit(1)

                    whatis(new_filename, new_section, basename, nb_of_so_redirections + 1)
                    break
            return

        # We only process ds (define string) macros at a line start
        # though they can appear in other contexts:
        elif text_line.startswith(".ds"):
            logging.debug(text_line)
            parts = text_line.split()
            defined_strings[parts[1]] = parts[2]

    if in_mandoc_section_name or in_mdoc_section_name:
        if parameters["Print type"]:
            if in_mandoc_section_name:
                if nb_of_so_redirections:
                    print(whatis_text + "|" + "so(" + str(nb_of_so_redirections) + "):man")
                else:
                    print(whatis_text + "|" + "man")
            elif nb_of_so_redirections:
                print(whatis_text + "|" + "so(" + str(nb_of_so_redirections) + "):mdoc")
            else:
                print(whatis_text + "|" + "mdoc")
        else:
            print(whatis_text)
    elif parameters["Print type"]:
        print(basename + " - " + "|" + "other")


################################################################################
def get_manpath_directories():
    """Return the list of directories in MANPATH"""
    manual_directories = []
    if os.environ["MANPATH"]:
        manual_directories = os.environ["MANPATH"].split(os.pathsep)
    else:
        if os.name == "posix":
            if os.path.isdir("/usr/share/man"):
                manual_directories.append("/usr/share/man")
            if os.path.isdir("/usr/local/man"):
                manual_directories.append("/usr/local/man")
            if os.path.isdir("/usr/local/share/man"):
                manual_directories.append("/usr/local/share/man")
        elif os.name == "nt":
            pnu_manpath = os.sep + "python" + os.sep + "man"
            appdata_path = os.sep + "appdata" + os.sep + "roaming"
            if os.environ["APPDATA"]:
                pnu_manpath = os.environ["APPDATA"] + pnu_manpath
            elif os.environ["HOMEPATH"]:
                pnu_manpath = os.environ["HOMEPATH"] + appdata_path + pnu_manpath
            elif os.environ["USERPROFILE"]:
                pnu_manpath = os.environ["USERPROFILE"] + appdata_path + pnu_manpath

            if os.path.isdir(pnu_manpath):
                manual_directories.append(pnu_manpath)

    return manual_directories


################################################################################
def show_section_contents(section):
    """Show the man pages in a section of the Manual"""
    for directory in get_manpath_directories():
        manual_section = directory + os.sep + "man" + section
        if os.path.isdir(manual_section):
            files = os.listdir(manual_section)
            files.sort()
            for name in files:
                if os.path.isfile(manual_section + os.sep + name):
                    basename = re.sub(r"\." + section + r"\.[A-Za-z0-9]*$", "", name)
                    whatis(manual_section + os.sep + name, section, basename, 0)


################################################################################
def main():
    """The program's main entry point"""
    program_name = os.path.basename(sys.argv[0])
    console_log_format = program_name + ": %(levelname)s: %(message)s"
    logging.basicConfig(format=console_log_format, level=logging.DEBUG)
    logging.disable(logging.INFO)

    process_environment_variables()
    arguments = process_command_line()

    if not arguments and not parameters["Files"]:
        show_manual_sections()
    else:
        if parameters["Files"]:
            for page in parameters["Files"]:
                basename = os.path.basename(page)
                section = re.sub(r"\.[A-Za-z0-9]*$", "", basename)
                basename = re.sub(r"\.[A-Za-z0-9]+$", "", section)
                section = re.sub(r"^.*\.", "", section)
                whatis(page, section, basename, 0)
        if arguments:
            for argument in arguments:
                show_section_contents(argument)

    sys.exit(0)


if __name__ == "__main__":
    main()
