# Version (https://www.python.org/dev/peps/pep-0440/#public-version-identifiers)
# Release versions: [major].[minor].[micro]
# Alpha versions: [major].[minor].[micro].dev[0,1,2...]
from importlib.metadata import version

__version__ = version("sizebot")
