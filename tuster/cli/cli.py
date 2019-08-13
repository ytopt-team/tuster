
import argparse
import os
import sys


def create_parser():
    parser = argparse.ArgumentParser(
        description='Tuster command line.')

    subparsers = parser.add_subparsers()

    # theta
    from tuster.system.theta import parser as theta_parser
    theta_parser.add_subparser(subparsers)

    return parser


def main():
    parser = create_parser()

    args = parser.parse_args()

    try:
        args.func(**vars(args))
    except AttributeError:
         parser.print_help()
