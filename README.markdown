# fortune.py

[http://github.com/goerz/fortune.py](http://github.com/goerz/fortune.py)

Author: [Michael Goerz](http://michaelgoerz.net)

Print a random, hopefully interesting, adage ("fortune"), selected from a
collection of fortune files

`fortune.py` is an extended implementation of the classic BSD Unix fortune
command. It combines the capabilities of the `strfile` command (which produces
the fortune index file) and the fortune command (which displays a random
fortune). It reads the traditional fortune program's text file format.

This code is licensed under the [GPL](http://www.gnu.org/licenses/gpl.html)

## Install ##

Store the `fortune.py` script anywhere in your `$PATH`.

## Usage ##

    Usage: fortune.py [OPTIONS] fortune_path

    Options:
      -h, --help            show this help message and exit
      -u, --update          Update the index files, instead of printing a fortune.
                            You must run this before you will be able to print
                            fortunes from the fortune files. This option serves
                            the same purpose as the strfile utility for the
                            traditional BSD fortune command. Note that the
                            generated index files are not compatible with the
                            format of the traditional index files. The generated
                            index files have the .pdat extension.
      -q, --quiet           When updating the index file, don't emit messages.
      -a, --all             Choose from all fortune files, including offensive
                            ones. Don't complain if you are offended!
      -o, --offensive       Choose only from offensive fortunes. Offensive
                            fortunes are those stored in files with filenames
                            ending in '-o'. Make absolutely sure that you want to
                            be offended!
      -e, --equal           Consider all fortune files to be of equal size, making
                            it equally likely for a fortune to be chosen from any
                            fortune file
      -f, --fortunefiles    Print out the list of files which would be searched,
                            but don't print a fortune.
      -l, --long            Show only long fortunes. See -n on how ''long'' is
                            defined in this sense.
      -w SECONDS_TO_WAIT, --wait=SECONDS_TO_WAIT
                            Wait before termination for an amount of time
                            calculated from the number of characters in the
                            message. This is useful if it is executed as part of
                            the logout procedure to guarantee that the message can
                            be read before the screen is cleared.
      -m PATTERN, --filter=PATTERN
                            Print out all fortunes which match the regular
                            expression pattern. The fortunes are printed to
                            standard output, while the names of the file from
                            which each fortune comes are printed to standard
                            error.  Either or both can be redirected; if standard
                            output is redirected to a file, the result is a valid
                            fortunes database file. If standard error is also
                            redirected to this file, the result is still valid,
                            but there will be ''bogus'' fortunes, i.e. the
                            filenames themselves, in parentheses. You may combine
                            this option with -o, -l, -s, -n, -i
      -i, --ignorecase      Ignore case for -m patterns.
      -s, --short           Show only short fortunes. See -n on how ''short'' is
                            defined in this sense.
      -n MAX_SHORTLENGTH    Set the longest fortune length (in characters)
                            considered to be ''short'' (the default is 160)

    If <fortune_path> is omitted, fortune looks at the FORTUNE_PATH environment
    variable for the paths. Different paths in FORTUNE_PATH are separated by ':'.
    An individual item inside the fortune_path can be a direct fortunefile, or a
    folder, in which case all fortune files inside the folder will be used. Any
    item may be preceded by a percentage, which is a number N between 0  and 99
    inclusive, followed by a %. If it is, there will be a N percent probability
    that a fortune will be picked from that file or directory. For items for which
    there is a percentage, the probability of a fortune being selected from any
    one of them is based on the relative number of fortunes it contains.

    The format of each fortune file is simple: All the fortunes appear in clear
    text, separated by a single line containing only a '%'. For example, the
    following is a fortune file containing two fortunes:

        186,282 miles per second:

        It isn't just a good idea, it's the law!
        %
        A bird in the hand makes it awfully hard to blow your nose.

    Before a fortune file can be used, you must generate an index file for it.
    This is a binary file that is used to select fortunes with more speed and
    efficiency.

    For more background information about the fortune utility look at
    http://en.wikipedia.org/wiki/Fortune_(Unix)

