import os
import sys
import stat
import datetime

from tuster.system.bebop.render import render


def add_subparser(subparsers):
    subparser_name = "bebop"
    function_to_call = main

    subparser = subparsers.add_parser(subparser_name)

    subparser.add_argument("-n", int)
    subparser.add_argument("--job-name", type=str)
    subparser.add_argument("--account", type=str)
    subparser.add_argument("--partition", type=str)
    subparser.add_argument("--nodes", type=int)
    subparser.add_argument("--ntasks-per-node", type=int)
    subparser.add_argument("--output", type=str)
    subparser.add_argument("--error", type=str)
    subparser.add_argument("--time", type=str)
    subparser.add_argument("exe", type=str)

    subparser.set_defaults(func=function_to_call)


def main(**kwargs):

    date = ("_".join(str(datetime.datetime.now()).split(" "))).split(".")[0]
    fname = f"tuster-{date}.sh"

    with open(fname, "w") as f:
        f.write(render(python_bin=os.path.dirname(sys.executable), **kwargs))

    # make the file executable
    os.chmod(fname, stat.S_IEXEC)

    os.system(f"sbatch {fname}")
