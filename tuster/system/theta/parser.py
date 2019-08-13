import argparse
import os
import sys
import datetime

from tuster.system.theta.render import render

def add_subparser(subparsers):
    subparser_name = 'theta'
    function_to_call = main

    subparser = subparsers.add_parser(subparser_name)

    subparser.add_argument('-q', type=str)
    subparser.add_argument('-A', type=str)
    subparser.add_argument('-t', type=int)
    subparser.add_argument('-n', type=int)
    subparser.add_argument('exe', type=str)

    subparser.set_defaults(func=function_to_call)


def main(**kwargs):

    date = ("_".join(str(datetime.datetime.now()).split(' '))).split('.')[0]
    with open(f'tuster-{date}.sh', 'w') as f:
        f.write(render(
            python_bin=os.path.dirname(sys.executable),
            **kwargs))