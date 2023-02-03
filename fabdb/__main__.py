import sys

from fabdb.cli import FabDBCLI, FabDBCLIConfig


if __name__ == "__main__":
    conf = FabDBCLIConfig()
    cli = FabDBCLI(conf)
    cli.run(sys.argv[1:])

