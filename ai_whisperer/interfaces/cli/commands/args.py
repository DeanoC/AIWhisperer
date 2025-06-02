import shlex
from typing import Any, Dict
def parse_args(argstr: str) -> Dict[str, Any]:
    """
    Parse a command argument string into positional args and options.
    Supports --key=value, --flag, and positional args.
    Returns a dict with 'args' (list) and 'options' (dict).
    """
    args = []
    options = {}
    tokens = shlex.split(argstr)
    for token in tokens:
        if token.startswith('--'):
            if '=' in token:
                key, value = token[2:].split('=', 1)
                options[key] = value
            else:
                options[token[2:]] = True
        else:
            args.append(token)
    return {'args': args, 'options': options}
