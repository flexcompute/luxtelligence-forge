import pathlib
import re
import luxtelligence_lnoi400_forge as lxt


def test_version():
    assert isinstance(lxt.__version__, str)
    assert lxt.__version__ == lxt.lnoi400().version
    pyproject = pathlib.Path("pyproject.toml")
    if pyproject.is_file():
        contents = pyproject.read_text()
        match = re.search('version = "([^"]*)"', contents)
        assert match and match.groups(1)[0] == lxt.__version__
