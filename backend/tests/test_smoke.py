"""Smoke test: the package is installed and importable."""

import jobmatch


def test_package_imports() -> None:
    assert jobmatch.__name__ == "jobmatch"


def test_main_runs(capsys) -> None:
    jobmatch.main()
    assert capsys.readouterr().out.strip() == "jobmatch"
