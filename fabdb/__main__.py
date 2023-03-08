from argparse import ArgumentParser
import sys

from fabdb.cli import FabDBCLI, FabDBCLIConfig
from fabdb.tui import FabDBApp


def main():
    # peek to see if we were called in interactive mode
    parser = ArgumentParser(add_help=False)
    parser.add_argument("action")
    parsed, _ = parser.parse_known_args()

    conf = FabDBCLIConfig()

    if parsed.action == "interactive":
        app = FabDBApp(conf)
        app.run()
    else:
        cli = FabDBCLI(conf)
        cli.run(sys.argv[1:])


if __name__ == "__main__":
    main()
