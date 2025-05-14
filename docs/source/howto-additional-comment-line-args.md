# How-to: parse your own command line arguments

You can use the `containup_cli()` function to parse command line arguments.
You will get a Config object that will give your arguments
as an array of strings in the `extra_args` property.

```bash
# replace containup-stack.py with the name of your script
./containup-stack.py up -- --origin_name=myproject --origin_version=3.5.8
```

In your script

```python
import argparse
import sys
from containup import containup_cli

# call our CLI parser
config = containup_cli()

# get your extra arguments (it's a list of string like sys.argv[:1])
extra_args = config.extra_args

# Then, you can parse them with, for example, Python's argparse :
parser = argparse.ArgumentParser(prog="mystack")
parser.add_argument("--origin_name")
parser.add_argument("--origin_version")

parsed = parser.parse_args(args=extra_args)
print("origin_name=", parsed.origin_name)
print("origin_name=", parsed.origin_version)

```
