import pytest

from gotime.providers import Provider


def test_provider():
    provider = Provider()
    with pytest.raises(NotImplementedError):
        provider.get_result(None, None)
