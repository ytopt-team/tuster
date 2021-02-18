import argparse


def create_parser():
    parser = argparse.ArgumentParser(description="Tuster command line.")

    subparsers = parser.add_subparsers()

    # theta
    from tuster.system.theta import parser as theta_parser

    theta_parser.add_subparser(subparsers)

    # thetagpu
    from tuster.system.thetagpu import parser as thetagpu_parser

    thetagpu_parser.add_subparser(subparsers)

    # bebop
    from tuster.system.bebop import parser as bebop_parser

    bebop_parser.add_subparser(subparsers)

    return parser


def main():
    parser = create_parser()

    args = parser.parse_args()

    try:
        args.func(**vars(args))
    except AttributeError:
        parser.print_help()
