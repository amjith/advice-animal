import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import click

from .api import Env

from .runner import Runner
from .workflow import BaseWorkflow, compare, TestWorkflow


# TODO checks-dir to ctx
@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.option("--checks-dir")
def list(checks_dir):
    for t in Runner(Env(Path()), Path(checks_dir)).iter_checks():
        print(t)


@main.command()
@click.option("--checks-dir")
def test(checks_dir):
    rv = 0
    for n, cls in Runner(Env(Path()), Path(checks_dir)).iter_check_classes():
        if (a_dir := Path(checks_dir, n, "a")).exists():
            inst = cls(Env(a_dir))
            assert inst.pred()  # it wants to run

            wf = TestWorkflow(Env(a_dir))

            with wf.work_in_branch("", "") as workdir:
                inst.apply(workdir)
                lrv = compare(Path(checks_dir, n, "b"), workdir)

                if cls(Env(workdir)).pred():
                    result = click.style("NOT DONE", fg="yellow")
                elif lrv:
                    result = click.style("FAIL", fg="red")
                else:
                    result = click.style("PASS", fg="green")

            click.echo(n.ljust(25) + result)
            rv |= int(lrv)
    return rv


@main.command()
@click.option("--checks-dir")
@click.option("-n", "--dry-run", is_flag=True)
# TODO a way to filter on confidence
@click.argument("target")
def trial(checks_dir, dry_run, target):
    env = Env(Path(target))
    wf = BaseWorkflow(env)

    for n, cls in Runner(env, Path(checks_dir)).iter_check_classes():
        inst = cls(env)
        if inst.pred():
            click.echo(click.style(n, fg="red") + " would make changes")
            if not dry_run:
                with wf.work_in_branch("advice-" + n) as workdir:
                    inst.apply(workdir)


if __name__ == "__main__":
    main()