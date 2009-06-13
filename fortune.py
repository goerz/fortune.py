#!/usr/bin/python
############################################################################
#    Copyright (C) 2008 by Michael Goerz                                   #
#    http://www.physik.fu-berlin.de/~goerz                                 #
#                                                                          #
#    This program is free software; you can redistribute it and/or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 3 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################
"""
This script is an extended implementation of the classic BSD Unix fortune
command. It combines the capabilities of the strfile command (which produces
the fortune index file) and the fortune command (which displays a random
fortune). It reads the traditional fortune program's text file format.
"""


import random
import os
import sys
import re
import cPickle as pickle
from optparse import OptionParser, IndentedHelpFormatter
from glob import glob
from time import sleep


_PICKLE_PROTOCOL = 2
INDEX_EXT = '.pdat'   #  file extension of index files
DEFAULT_LENGTH = 160  #  default number of characters a ''short'' fortune
                      #  can have at maximum
ATTEMPTS = 10000      #  number of attempts that will be made to find an 
                      #  appropriate fortune, before the program gives up



def get_random_fortune(fortunepaths, weighted=True, offensive=None, 
                       min_length=0, max_length=None):
    """
    Get a random fortune from a fortune file found in the fortunepaths . 
    Barfs if the corresponding index file isn't present.

    If 'weighted' is True, the likelihood for a fortune file to be selected
    is proportional to the number of fortunes in a file. If 'weighted' is
    False, all fortune files are equally likely to be picked.

    The fortunepaths array may also contain percentage makers, e.g.
            ['10%', 'fortunes', '80%', 'fortunes2', 'limerick' ]
    If these are present, they are taken into consideration when calculating
    the weights. Fortune files for which there is no percentage given, are
    still weighted by the number of fortunes they contain.

    If 'offensive' is None, a fortune will be selected that may be offensive
    or non-offensive. If 'offensive' is True, only offensive fortunes will 
    be picked, if it is False, only non-offensive fortunes will be picked.
    An offensive fortune is defined as one appearing in a fortune file
    who's name ends in '-o'

    The length of the fortune that is returned will be between min_length and
    max_length. 
    """
    # get list of fortune files
    percentages, fortune_files = fortune_files_from_paths(fortunepaths, 
                                                          offensive)
    # choose fortune_file
    weights = None
    if weighted:
        weights = []
        for fortune_file in fortune_files:
            data = fortune_file_data(fortune_file)
            weights.append(len(data))
        weights = adjust_weights_with_percentages(weights, percentages)
    attempt = 0
    while True:
        fortune_file = rselect_fortune_file(fortune_files, weights)
        data = fortune_file_data(fortune_file)
        (start, length) = random.choice(data)
        if (length < min_length 
        or (max_length is not None and length > max_length)): 
            attempt += 1
            if attempt > ATTEMPTS:
                print >> sys.stderr,  "I've given up on finding a fortune " \
                             "that matches your criteria. They are too strict."
                return ""
            continue
        ffh = open(fortune_file, 'rU')
        ffh.seek(start)
        fortunecookie = ffh.read(length)
        ffh.close()
        return fortunecookie



def adjust_weights_with_percentages(weights, percentages):
    """ Adjust the weights to conform to the percentages 
        If a percentage is given, the weight is adjusted so that it's the 
        percentage of the sum of all weights. All other weights (where
        percentage is None) are rescaled (keeping their relative magnitude
        to each other) so that the total sum of all weights stays constant
    """
    sum_of_weights = 0
    sum_of_free_weights = 0 # free weight: percentage is None
    sum_of_percentages = 0
    result = []
    for weight, percentage in zip(weights, percentages):
        sum_of_weights += weight
        if percentage is None:
            sum_of_free_weights += weight
        else:
            sum_of_percentages += percentage
    for weight, percentage in zip(weights, percentages):
        if percentage is None:
            result.append( int(round(
                                ( weight 
                                  * (100 - sum_of_percentages)
                                  * sum_of_weights)
                                / float(100 * sum_of_free_weights) 
                              )) )
        else:
            result.append(int(round((percentage * sum_of_weights) / 100.0)))
    return result



def fortune_files_from_paths(fortunepaths, offensive=None):
    """ Return (percentages, fortune_files)
    
        fortune_files is a list of all fortune files found in fortunepaths.
        
        fortunepaths may also contain percentage markers intermixed with
        actual paths. For example, fortunepaths may be
            ['10%', 'fortunes', '80%', 'fortunes2', 'limerick' ]
 
        'percentages' is an array of equal size as fortune_files, that 
        contains float values corresponding to the given percentages or
        None if there was no percentage given for a path. If percentages
        were given for all paths, they will be rescaled so that they add
        up to 100.0

        If there is more than one fortune file in a single fortunepath,
        and there is a percentage given for that fortunepath, the 
        percentage is split between all the fortune files found in that
        fortunepath.

        If 'offensive' is None, include offensive and non-offensive fortune
        files. If 'offensive' is True, include only offensive fortune files, 
        if it is False, include only non-offensive fortune files.
        An offensive fortune fortune files is defined as who's name ends in '-o'
    """
    percentage_pattern = re.compile('([0-9]{1,2})%')
    fortune_files = []
    percentages = []
    percentage = None
    for path in fortunepaths:
        percentage_match = percentage_pattern.match(path)
        if percentage_match:
            percentage = percentage_match.group(1) 
            continue
        else:
            if os.path.isdir(path):
                files_in_path = [filename[:-len(INDEX_EXT)] for filename 
                                in glob(os.path.join(path, "*"+INDEX_EXT))]
                if offensive is not None:
                    files_in_path = [fortune_file for fortune_file 
                                     in files_in_path
                                     if not xor(fortune_file.endswith('-o'),
                                                offensive)]

                fortune_files += files_in_path
                number_of_added_files = float(len(fortune_files) 
                                              - len(percentages))
                while len(percentages) < len(fortune_files):
                    if percentage is not None:
                        percentages.append(int(percentage) 
                                           / number_of_added_files)
                    else:
                        percentages.append(None)
            else:
                if offensive is not None:
                    if xor(path.endswith('-o'), offensive):
                        path = None
                if path is not None: 
                    fortune_files.append(path) # path is file
                    if percentage is not None:
                        percentages.append(float(percentage))
                    else:
                        percentages.append(None)
            percentage = None
    return (check_percentages(percentages), fortune_files)



def check_percentages(percentages):
    """ Check percentages for validity
        
        percentages is an array where each array element is either a 
        percentage value or None. The percentage values must add up to 
        no more than 100.0. Negative values count as positive.

        If there are no None-values and the percentages do not add up
        to 100.0, they are rescaled so that they do.

        None-values stay None 

        The result is a copy of percentages were all values that are 
        not None are floats and may have been rescaled.
    """
    # check that sum of percentages is not more than 100%
    try:
        given_values = [abs(value) for value in percentages 
                                        if value is not None]
        percentage_sum = sum(given_values)
    except ValueError:
        print >> sys.stderr, "Percentages are in incompatible formats"
        sys.exit(1)
    if percentage_sum > 100.0:
        print >> sys.stderr, "Percentages add up to more than a hundred"
        sys.exit(1)
    
    # make everything that's not None into floats, rescale if applicable
    if len(percentages) == len(given_values): # no None-values
        # convert all values to float and rescale if necessary
        try:
            percentages = [abs((float(percentage) * (100.0 / percentage_sum)))
                           for percentage in percentages]
        except ValueError:
            print >> sys.stderr, "Percentages cannot be converted to float"
            sys.exit(1)
    else:
        for i, percentage in enumerate(percentages):
            if percentage is not None:
                try:
                    percentages[i] = abs(float(percentage))
                except ValueError:
                    print >> sys.stderr, \
                                      "Percentages cannot be converted to float"
                    sys.exit(1)
    return percentages



def filter_fortunes(fortunepaths, pattern, ignorecase=True, offensive=None,
                    min_length=0, max_length=None):
    """ Print out all fortunes which match the regular expression pattern. 

        If ignorecase is True, the pattern is taken as case-insensitive.

        The fortunes are printed to standard output, while the names of the file
        from which each fortune comes are printed to standard error. Either or
        both can be redirected; if standard output is redirected to a file, the
        result is a valid fortunes database file. If standard error is also
        redirected to this file, the result is still valid, but there will be
        ''bogus'' fortunes, i.e. the filenames themselves, in parentheses.

        In addition to the pattern, the selected fortunes are constrained by
        the offensive, min_length, and max_length parameters.
    """
    regex_filter = re.compile(pattern)
    if ignorecase:
        regex_filter = re.compile(pattern, re.I)
    percentages, fortune_files = fortune_files_from_paths(fortunepaths, 
                                                          offensive)

    # "first" fortune file (or up to wherever the first match is)
    # The reason for having to handle the first match separately is to get
    # the formatting of the output right.
    found_first_match = False
    while not found_first_match:
        fortune_file = fortune_files.pop(0)
        print >> sys.stderr, "(" + os.path.split(fortune_file)[1] + ")"
        print >> sys.stderr, "%"
        sys.stderr.flush()
        fortunes = read_fortunes(open(fortune_file, 'rU'))
        while not found_first_match:
            try:
                start, length, fortune = fortunes.next()
                if (length < min_length 
                or (max_length is not None and length > max_length)):
                    continue
                if regex_filter.search(fortune):
                    print fortune
                    found_first_match = True
            except StopIteration:
                break
    for start, length, fortune in fortunes: # remaining fortunes of "first" file
        if (length < min_length 
        or (max_length is not None and length > max_length)):
            continue
        if regex_filter.search(fortune):
            print "%"
            sys.stdout.write(fortune)
    sys.stdout.flush()

    # remaining fortune files
    for fortune_file in fortune_files: # original "first" item(s) were popped!
        print >> sys.stderr, "%"
        print >> sys.stderr, "(" + os.path.split(fortune_file)[1] + ")"
        sys.stderr.flush()
        fortunes = read_fortunes(open(fortune_file, 'rU'))
        for start, length, fortune in fortunes: # starting a second!
            if (length < min_length 
            or (max_length is not None and length > max_length)):
                continue
            if regex_filter.search(fortune):
                print "%"
                sys.stdout.write(fortune)
        sys.stdout.flush()



def xor(bool_a, bool_b):
    """ Logical XOR between boolean variables bool_a and bool_b """
    return ((bool_a and not bool_b) or (bool_b and not bool_a))



def fortune_file_data(fortune_file):
    """ Return the pickled index for fortune_file """
    fortune_index_file = str(fortune_file) + INDEX_EXT
    if not os.path.exists(fortune_index_file):
        raise ValueError, 'Can\'t find file "%s"' % fortune_index_file
    fortune_index = open(fortune_index_file)
    data = pickle.load(fortune_index)
    fortune_index.close()
    return data



def rselect_fortune_file(fortune_files, weights=None):
    """ Return a random element from fortune_files

        If weights is not given, all elements of fortune_files are equally
        likely to be returned.
        If weights is given, it must be an array of the same length as 
        fortune_files, consisting of integers. The ratio of the integer at 
        a position to the sum of all integers is the probability that the
        element at the same position in fortune_files is returned.
    """
    if weights is None:
        return random.choice(fortune_files)
    # find sum of weights
    total = 0
    for weight in weights:
        total += weight
    # choose randomly
    rand_limit = random.randint(1, total)
    total = 0
    i = 0
    for weight in weights:
        total += weight
        if total >= rand_limit:
            return fortune_files[i]
        i += 1
    raise Exception, "Couldn't select a fortune file"



def read_fortunes(fortune_file):
    """ Return iterator yielding tuples (startline, length, fortune)
        where startline is the line nr in the fortune file where the
        fortune starts, length is the number of lines of the fortune,
        and fortune is the text of the fortune as a string.
    """
    fortune_lines = []
    start = -1
    pos = 0
    for line in fortune_file:
        if line == "%\n":
            if pos == 0: # "%" at top of file. Skip it.
                continue
            fortune = "".join(fortune_lines)
            if fortune != "": 
                yield (start, pos - start, fortune)
            fortune_lines = []
            start = -1
        else:
            if start == -1:
                start = pos
            fortune_lines.append(line)
        pos += len(line)

    fortune = "".join(fortune_lines)
    if fortune != "": 
        yield (start, pos - start, fortune)



def make_fortune_data_file(fortunepaths, quiet=False):
    """
    Create or update the index file for a fortune cookie file.
    """
    fortune_files = []
    for path in fortunepaths:
        if os.path.isdir(path):
            fortune_files += [filename for filename 
                            in glob(os.path.join(path, "*"))
                            if not filename.endswith(INDEX_EXT)
                            ]
        else:
            fortune_files.append(path) # path is a file
    for fortune_file in fortune_files:

        fortune_index_file = fortune_file + INDEX_EXT
        if not quiet:
            print 'Updating "%s" from "%s"...' \
                                            % (fortune_index_file, fortune_file)

        data = []
        shortest = sys.maxint
        longest = 0
        for start, length, fortune in read_fortunes(open(fortune_file, 'rU')):
            data += [(start, length)]
            shortest = min(shortest, length)
            longest = max(longest, length)

        fortune_index = open(fortune_index_file, 'wb')
        pickle.dump(data, fortune_index, _PICKLE_PROTOCOL)
        fortune_index.close()

        if not quiet:
            print 'Processed %d fortunes.\nLongest: %d\nShortest %d' % \
                (len(data), longest, shortest)



def main():
    """
    Main program.
    """
    class MyIndentedHelpFormatter(IndentedHelpFormatter):
        """ Slightly modified formatter for help output: allow paragraphs """
        def format_paragraphs(self, text):
            """ wrap text per paragraph """
            result = ""
            for paragraph in text.split("\n"):
                result += self._format_text(paragraph) + "\n"
            return result
        def format_description(self, description):
            """ format description, honoring paragraphs """
            if description:
                return self.format_paragraphs(description) + "\n"
            else:
                return ""
        def format_epilog(self, epilog):
            """ format epilog, honoring paragraphs """
            if epilog:
                return "\n" + self.format_paragraphs(epilog) + "\n"
            else:
                return ""
    usage = 'Usage: %s [OPTIONS] fortune_path' % os.path.basename(sys.argv[0])
    arg_parser = OptionParser(usage=usage, formatter=MyIndentedHelpFormatter())
    arg_parser.description = "Print a random, hopefully interesting, adage " \
        "(\"fortune\"), selected from a collection of fortune files found " \
        "in fortune_path.\n\n" \
        "%s " % str(os.path.basename(sys.argv[0])) \
        + 'is an extended implementation of ' \
        'the classic BSD Unix fortune command. It combines the capabilities ' \
        'of the strfile command (which produces the fortune index file) and ' \
        'the fortune command (which displays a random fortune). It reads ' \
        'the traditional fortune program\'s text file format. ' \
        "For more information about the fortune files, and the accompanying " \
        "fortune index files, see below." 
    arg_parser.add_option('-u', '--update', action='store_true', dest='update',
                          help='Update the index files, instead of printing a '
                               'fortune. You must run this before you will be '
                               'able to print fortunes from the fortune files. '
                               'This option serves the same purpose as the '
                               'strfile utility for the traditional BSD '
                               'fortune command. Note that the generated '
                               'index files are not compatible with the format '
                               'of the traditional index files. The generated '
                               'index files have the %s extension.' %  INDEX_EXT
                               )
    arg_parser.add_option('-q', '--quiet', action='store_true', dest='quiet',
                          help="When updating the index file, don't emit " 
                               "messages.")
    arg_parser.add_option('-a', '--all', action='store_true', dest='use_all',
                          help="Choose from all fortune files, including "
                          "offensive ones. Don't complain if you are offended!")
    arg_parser.add_option('-o', '--offensive', action='store_true', 
                          dest='offensive',
                          help="Choose only from offensive fortunes. "
                               "Offensive fortunes are those stored in files "
                               "with filenames ending in '-o'. Make absolutely "
                               "sure that you want to be offended!")
    arg_parser.add_option('-e', '--equal', action='store_true',
                          dest='equal_size',
                          help="Consider all fortune files to be of equal " 
                               "size, making it equally likely for a "
                               "fortune to be chosen from any fortune file")
    arg_parser.add_option('-f', '--fortunefiles', action='store_true',
                          dest='list_fortunefiles',
                          help="Print out the list of files which would be " 
                               "searched, but don't print a fortune. ")
    arg_parser.add_option('-l', '--long', action='store_true', dest='use_long',
                          help="Show only long fortunes. See -n on how " 
                               "''long'' is defined in this sense.")
    arg_parser.add_option('-w', '--wait', action='store', type=int, 
                          dest='seconds_to_wait',
                          help="Wait before termination for an amount of time "
                               "calculated from the number of characters in "
                               "the message. This is useful if it is executed "
                               "as part of the logout procedure to guarantee "
                               "that the message can be read before the screen "
                               "is cleared.")
    arg_parser.add_option('-m', '--filter', action='store', dest='pattern',
                          help="Print out all fortunes which match the " 
                               "regular expression pattern.\n" 
                               "The fortunes are printed to standard output, " 
                               "while the names of the file from which each " 
                               "fortune comes are printed to standard " 
                               "error.  Either or both can be redirected; " 
                               "if standard output is redirected to a file, " 
                               "the result is a valid fortunes database " 
                               "file. If standard error is also redirected " 
                               "to this file, the result is still valid, " 
                               "but there will be ''bogus'' fortunes, i.e. " 
                               "the filenames themselves, in parentheses.\n" 
                               "You may combine this option with -o, -l, " 
                               "-s, -n, -i")
    arg_parser.add_option('-i', '--ignorecase', action='store_true', 
                          dest='ignorecase',
                          help="Ignore case for -m patterns.")
    arg_parser.add_option('-s', '--short', action='store_true', 
                          dest='use_short',
                          help="Show only short fortunes. See -n on how " 
                               "''short'' is defined in this sense.")
    arg_parser.add_option('-n', action='store', dest='max_shortlength',
                          help="Set the longest fortune length (in " 
                               "characters) considered to be ''short'' " 
                               "(the default is %s)" % DEFAULT_LENGTH)

    arg_parser.epilog = 'If <fortune_path> is omitted, fortune looks at ' \
        'the FORTUNE_PATH environment variable for the paths. Different ' \
        'paths in FORTUNE_PATH are separated by \':\'.\n' \
        'An individual item inside the fortune_path can be a direct fortune' \
        'file, or a folder, in which case all fortune files inside the ' \
        'folder will be used. Any item may be preceded by a percentage, '\
        'which is a number N between 0  and 99 inclusive, followed by a %. ' \
        'If it is, there will be a N percent probability that a fortune ' \
         'will be picked from that file or directory. For items for which ' \
         'there is a percentage, the probability of a fortune being selected ' \
         'from any one of them is based on the relative number of fortunes ' \
         'it contains.\n\n' \
         'The format of each fortune file is simple: All the fortunes appear ' \
         'in clear text, separated by a single line containing only a ' \
         '\'%\'. For example, the following is a fortune file containing two ' \
         'fortunes:\n\n' \
         '    186,282 miles per second:\n\n' \
         '    It isn\'t just a good idea, it\'s the law!\n' \
         '    %\n' \
         '    A bird in the hand makes it awfully hard to blow your nose.\n\n' \
         'Before a fortune file can be used, you must generate an index ' \
         'file for it. This is a binary file that is used to select ' \
         'fortunes with more speed and efficiency.\n\n' \
         'For more background information about the fortune utility ' \
         'look at http://en.wikipedia.org/wiki/Fortune_(Unix)'
         

    options, args = arg_parser.parse_args(sys.argv)

    if len(args) >= 2:
        fortunepaths = args[1:]
    else:
        try:
            fortunepaths = os.environ['FORTUNE_PATH'].split(':')
        except KeyError:
            print >> sys.stderr, "Missing fortune files"
            print >> sys.stderr, "Try %s --help" % os.path.basename(sys.argv[0])
            sys.exit(1)

    if options.use_all:
        offensive = None
    elif options.offensive:
        offensive = True
    else:
        offensive = False

    if options.use_short:
        minlength = 0
        maxlength = DEFAULT_LENGTH 
        if not options.max_shortlength is None:
            maxlength = int(options.max_shortlength)
    elif options.use_long:
        minlength = DEFAULT_LENGTH 
        if not options.max_shortlength is None:
            minlength = int(options.max_shortlength)
        maxlength = None
    else:
        minlength = 0
        maxlength = None

    try:
        # Update Mode
        if options.update:
            make_fortune_data_file(fortunepaths)

        # Listing Fortune Files Mode
        elif options.list_fortunefiles:
            percentages, fortune_files = fortune_files_from_paths(fortunepaths,
                                                                  offensive)
            for filename in fortune_files:
                print filename

        # Filtering Mode
        elif not options.pattern is None:
            filter_fortunes(fortunepaths, options.pattern, 
                            ignorecase=options.ignorecase, 
                            offensive=offensive)
                
        # Printing Fortunes Mode
        else:
            sys.stdout.write(get_random_fortune(
                fortunepaths, 
                offensive=offensive,
                weighted=(not options.equal_size),
                min_length=minlength,
                max_length=maxlength) )

    except ValueError, msg:
        print >> sys.stderr, msg
        sys.exit(1)

    if not options.seconds_to_wait is None:
        sleep(options.seconds_to_wait)

    sys.exit(0)

if __name__ == '__main__':
    main()
