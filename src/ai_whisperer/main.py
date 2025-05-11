import sys
from .cli import main

if __name__ == "__main__":
    commands = main()
    for command in commands:
        command.execute()
    sys.exit(0)
