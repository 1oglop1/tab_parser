import argparse
import csv
import os
import sys


def sections(csv_file_object):
    """
    Parse input detail file and return tuple(day,records) generator
    :param csv_file_object: FileDescriptor object
    :rtype: tuple(day,records)
    """
    day_records = {}
    timestamp = ''
    r = csv.reader(csv_file_object, delimiter='\n')
    for line in r:

        # if line is not empty or '\n'
        if line:
            # input entry: type = value
            # split entry by '='
            # [type, value]
            entry = line[0].split('=')
            try:
                # try to pars entries, if this fails it parsing timestamp and creates new section
                el = entry[0].strip() # left side of =
                er = entry[1].strip() # = right side of
                day_records[el] = er.strip('"') # strip out quotes


            except IndexError:
                # for timestamp
                timestamp = entry[0]

        else:
            # update the called station
            mac, ssid = day_records['Called-Station-Id'].split(":")
            day_records['Called-Station-Id:mac'] = mac
            day_records['Called-Station-Id:ssid'] = ssid
            # return current day
            yield (timestamp, day_records)




def selected_sections(sections_dict, sec_names_list):
    """
    Take arguments and return generator of values from section
    :param sections_dict: dictionary from {timestamp:section}
    :param sec_names_list: list of sections to be selected from arguments
    :rtype: [record, record, record]
    """
    for section in sec_names_list[1:]:
        # print(sections_dict[section])
        try:
            yield sections_dict[section]
        except KeyError:
            # TODO - handle empty parameter
            # print(section, 'Not is recorded for current day', file=sys.stderr)
            yield '--'


def one_file_log(logfile, args):
    """
    Processing of one file
    :param logfile: input file
    :param args: cmdline arguments entries
    :rtype: list -> [timestamp, r1, r2, r..]
    """

    # vstup ( '13:30 pon', {'userame':'jarda', 'IP':'10.0.0.0'}
    for day, day_records in sections(logfile):
        log_records = [day]
        log_records.extend(selected_sections(day_records, args.entries))
        yield log_records
    # [ [time, r1, r2], [time, z`, z2] ]


def main():
    """The main function of tab2csv parser"""

   # parsing commandline arguments
    parser = argparse.ArgumentParser(
        argument_default=argparse.SUPPRESS,
        description='==== tab2csv log parser ====')

    parser.add_argument(
        '-entries', '-e', default=['User-Name', 'Called-Station-Id', 'Calling-Station-Id'],
        nargs='*',
        metavar='LOG-ENTRY',
        help='records to be displayed')

    parser.add_argument(  # will be printing to screen or to logfile
        '-log', default=sys.stdout, type=argparse.FileType('w'),
        help='the file where the sorted output should be written')

    parser.add_argument(
        'file', default=None,
        metavar='FILE',
        nargs='?',
        help='file to parse from or directory containing files'
    )

    parser.add_argument(
        '-sort', '-s', default='TimeStamp',
        metavar='LOG-ENTRY',
        help='sort by LOG-ENTRY'
    )
    args = parser.parse_args()


    # strip unwanted characters from log-entries
    if args.entries:
        args.entries = list(map(lambda x: x.strip(',;'), args.entries))
        args.entries.insert(0, 'TimeStamp')

    # sort by what? default TimeStamp
    try:
        sort_by = args.entries.index(args.sort)
    except ValueError:
        print(args.sort, 'is missing in entries', file=sys.stderr)

    # open one file
    try:
        with open(args.file) as logfile:

            # head line of CSV
            args.log.write('{entr}\n'.format(entr=','.join(args.entries)))

            list_of_records = list(one_file_log(logfile, args))  # list of lists[ [time1,r1,r2], [time2,r1,r2]..]

            sorted_list = sorted(list_of_records, key=lambda x: x[sort_by], reverse=False)  # sort by what
            # concatenate list of lists to one list of strings ["time1,r1,r2", "time2,r1,r2"]
            one_list = list(map(','.join, sorted_list))
            # write everything to log file
            args.log.write('\n'.join(one_list))
            args.log.write('\n')

    except IsADirectoryError:
        # processing whole directory
        list_of_files = os.listdir(args.file)
        os.chdir(args.file)
        print(list_of_files)

        for file in list_of_files:
            with open(file, 'r') as logfile:
                list_of_records = list(one_file_log(logfile, args))  # sort(key=lambda tmp: tmp[1], reverse=False)

                sorted_list = sorted(list_of_records, key=lambda x: x[sort_by], reverse=False)
                kk = list(map(','.join, sorted_list))
                args.log.write('\n'.join(kk))
                args.log.write('\n')

    except FileNotFoundError:

        print(args.file, 'does not exist', file=sys.stderr)
    except TypeError:
        parser.print_usage()

    args.log.close()


if __name__ == "__main__":
    main()
