# Installation
pip install [pnu-mtoc](https://pypi.org/project/pnu-mtoc/)

# MTOC(1)

## NAME
mtoc - show Manual table of contents

## SYNOPSIS
**mtoc**
\[-f|--file|--whatis FILE\]
\[-n|--no MACROS\]
\[--Dq\]
\[--Pa|--PaSq\]
\[--PaDq\]
\[--Xr\]
\[--debug\]
\[--help|-?\]
\[--version\]
\[--\]
\[SECTION ...\]

## DESCRIPTION
The **mtoc** utility shows the [Manual](https://www.freebsd.org/cgi/man.cgi) table of contents.

Without arguments, it will list the Manual sections listed in [man man](https://www.freebsd.org/cgi/man.cgi?query=man).

With arguments, it will list the contents of the requested Manual sections in [whatis(1)](https://www.freebsd.org/cgi/man.cgi?query=whatis) format.

The display can be a little bit improved over standard whatis format by using the *--Dq*, *--Pa*, *--PaSq*, *--PaDq* and *--Xr* options,
in order to interpret the corresponding [mdoc(7)](https://www.freebsd.org/cgi/man.cgi?query=mdoc&sektion=7) macros.

It can also be used as a database-less substitute of whatis, by using the *-f*, *--file* or *--whatis* options on a Manual page's pathname.

It is possible to discard [man(7)](https://www.freebsd.org/cgi/man.cgi?query=man&sektion=7)
or [mdoc(7)](https://www.freebsd.org/cgi/man.cgi?query=mdoc&sektion=7) pages
by using the *-n* or *--no* options with a *man* or *mdoc* parameter.

The *-f* and *-n* options can be used multiple times.

### OPTIONS
Options | Use
------- | ---
-f\|--file\|--whatis FILE|Process a specific file, like whatis(1)
-n\|--no MACROS|Discard man or mdoc macros
--Dq|Interpret .Dq (double quotes) macros
--Pa\|--PaSq|Interpret .Pa (path) macros as single quoted strings
--PaDq|Interpret .Pa (path) macros as double quoted strings
--Xr|Interpret .Xr (cross reference) macros
--debug|Enable debug mode
--help\|-?|Print usage and a short help message and exit
--version|Print version and exit
--|Options processing terminator

## ENVIRONMENT
The **MTOC_DEBUG** environment variable can also be set to any value to enable debug mode.

The **mtoc** utility uses the **MANPATH** environment variable to find man pages.
It provides default values both for Unix-like and Windows operating systems.

Locale man pages can be processed if the path where they are stored is added to **MANPATH**.

Under Windows, the command can use the **APPDATA**, **HOMEPATH** and **USERPROFILE** environment variables to find man pages.

## EXIT STATUS
The **mtoc** utility exits 0 on success, and >0 if an error occurs.

## SEE ALSO
[man(1)](https://www.freebsd.org/cgi/man.cgi?query=man),
[whatis(1)](https://www.freebsd.org/cgi/man.cgi?query=whatis),
[apropos(1)](https://www.freebsd.org/cgi/man.cgi?query=apropos),
[man(7)](https://www.freebsd.org/cgi/man.cgi?query=man&sektion=7),
[mandoc_char(7)](https://www.freebsd.org/cgi/man.cgi?query=mandoc_char&sektion=7),
[mdoc(7)](https://www.freebsd.org/cgi/man.cgi?query=mdoc&sektion=7),
[roff(7)](https://www.freebsd.org/cgi/man.cgi?query=roff&sektion=7)

## STANDARDS
The **mtoc** utility is not a standard UNIX/POSIX command.

It tries to follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for [Python](https://www.python.org/) code.

## HISTORY
This utility was made for [The PNU project](https://github.com/HubTou/PNU) in order to explore providing a manual under non-Unix operating systems.
This turned out to be way more complex than anticipated, forcing me to delve much more deeply in [roff(7)](https://www.freebsd.org/cgi/man.cgi?query=roff&sektion=7) macros than originally intended!

## LICENSE
This utility is available under the [3-clause BSD license](https://opensource.org/licenses/BSD-3-Clause).

## AUTHORS
[Hubert Tournier](https://github.com/HubTou)

## CAVEATS
The order of names in a man page is sorted alphabetically, which sometimes differ from whatis(1) output.
I couldn't find the logic behind whatis behaviour...

It isn't currently possible to process:
* architecture-dependent man pages (for example, in /usr/share/man/man[48]/{aarch64, amd64, arm, i386, powerpc}
* already uncompressed man pages (for example, in /usr/share/man/cat[1-9]

