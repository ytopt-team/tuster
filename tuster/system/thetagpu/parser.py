import datetime
import os
import stat
import sys

from tuster.system.thetagpu.render import render


def add_subparser(subparsers):
    subparser_name = "thetagpu"
    function_to_call = main

    subparser = subparsers.add_parser(subparser_name)

    subparser.add_argument("-q", type=str)
    subparser.add_argument("-A", type=str)
    subparser.add_argument("-t", type=int)
    subparser.add_argument("-n", type=int)
    subparser.add_argument("--gpu-per_task", type=int, default=8)
    subparser.add_argument("--cpu-per-task", type=int, default=8)
    subparser.add_argument(
        "env", type=str, help="Path to a bash script to initialize the environment."
    )
    subparser.add_argument("exe", type=str, help="Executable.")

    subparser.set_defaults(func=function_to_call)


def main(**kwargs):

    date = ("_".join(str(datetime.datetime.now()).split(" "))).split(".")[0]
    fname = f"tuster-{date}.sh"

    with open(fname, "w") as f:
        f.write(render(python_bin=os.path.dirname(sys.executable), **kwargs))

    # make the file executable
    os.chmod(fname, stat.S_IEXEC)

    # os.system(f"qsub {fname}")
