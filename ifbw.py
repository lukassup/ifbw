#!/usr/bin/env python

import time

from argparse import ArgumentParser
from os import system


# Parameter parsing
argparser = ArgumentParser()
argparser.add_argument(
    "-n",
    metavar="ITERATIONS",
    dest="iterations",
    default=0,
    help="iterations to perform before exiting (default: 0 (infinite))"
)
argparser.add_argument(
    "-i",
    "--interval",
    metavar="SECONDS",
    default=1,
    help="interval between measurements"
)
argparser.add_argument(
    metavar="INTERFACE",
    dest="interface_list",
    nargs="*",
    default="all",
    help="list of interfaces separated by spaces (default: all)"
)
argparser.add_argument(
    "-c",
    "--color",
    action="store_const",
    const="True",
    dest="color",
    help="turn on colors (default: off)"
)
argparser.add_argument(
    "-d",
    action="store_const",
    const="True",
    dest="debug",
    help="turn on debug mode (developers only)"
)

arguments = argparser.parse_args()
if arguments.debug:
    print(arguments)


class ANSI(object):
    """ANSI terminal escape codes"""

    black = "\033[30m"
    red = "\033[31m"
    green = "\033[32m"
    yellow = "\033[33m"
    blue = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"
    l_grey = "\033[37m"
    white = "\033[39m"
    d_grey = "\033[90m"
    l_red = "\033[91m"
    l_green = "\033[92m"
    l_yellow = "\033[93m"
    l_blue = "\033[94m"
    l_magenta = "\033[95m"
    l_cyan = "\033[96m"
    reset = "\033[0m"


def gather_interface_data():
    """Function for gathering data from system counters"""

    with open("/proc/net/dev") as datafile:
        # Skip the headers
        datafile.readline()
        datafile.readline()

        interfaces = {}
        for line in datafile:
            interface_info = line.split()
            interface = interface_info[0].split(":")[0]
            # check if reading info about an interface we're interested in
            if (interface not in arguments.interface_list and
                    "all" != arguments.interface_list):
                continue
            interfaces[interface] = {
                    "bytes_received": int(interface_info[1]),
                    "packets_received": int(interface_info[2]),
                    "bytes_sent": int(interface_info[9]),
                    "packets_sent": int(interface_info[10]),
                }

    return interfaces


def humanize(data):
    """Function for making large data numbers more human-readable"""

    data = float(data)
    order = 0  # of magnitude - index for the array below
    units = ["B", "kB", "MB", "GB", "TB", "PB"]
    while True:
        if data > 2 ** 10:
            data /= 2 ** 10
            order += 1
        else:
            break

    return {"amount": data, "units": units[order]}


def clear_line():
    print("\033[K", sep="", end="")


def print_rates():
    """Function that calculates the rates and prints them"""

    counters_before = gather_interface_data()
    time.sleep(float(arguments.interval))
    counters_after = gather_interface_data()

    # loop through interfaces that data has been collected about
    for interface in counters_before:

        # Calculate differences
        bytes_received = (counters_after[interface]["bytes_received"] -
                          counters_before[interface]["bytes_received"])
        bytes_sent = (counters_after[interface]["bytes_sent"] -
                      counters_before[interface]["bytes_sent"])

        # Data rates per second
        bytes_received_rate = bytes_received / float(arguments.interval)
        bytes_sent_rate = bytes_sent / float(arguments.interval)

        # Print the result
        print(("{}{:>12}{}: "
               "{}{:<4}{}: {:>8.2f} {:>2}/s, "
               "{}{:<4}{}: {:>8.2f} {:>2}/s").format(
                  ANSI.l_yellow if arguments.color else "",
                  interface,
                  ANSI.reset if arguments.color else "",
                  ANSI.red if arguments.color else "",
                  "down",
                  ANSI.reset if arguments.color else "",
                  humanize(bytes_received_rate)["amount"],
                  humanize(bytes_received_rate)["units"],
                  ANSI.green if arguments.color else "",
                  "up",
                  ANSI.reset if arguments.color else "",
                  humanize(bytes_sent_rate)["amount"],
                  humanize(bytes_sent_rate)["units"]
              ))


def hide_stdin():
    """Hide standard input"""
    system("stty -echo")


def show_stdin():
    """Show standard input"""
    system("stty echo")


def main():
    """Main loop"""

    if arguments.iterations:
        for iteration in range(0, int(arguments.iterations)):
            # clear_line()
            hide_stdin()
            print_rates()
    else:
        while True:
            # clear_line()
            hide_stdin()
            print_rates()

    show_stdin()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("", end="\r")
