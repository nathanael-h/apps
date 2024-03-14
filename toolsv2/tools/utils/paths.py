#!/usr/bin/env python3

from pathlib import Path

from git import Repo

APPS_REPO_ROOT = Path(Repo(__file__, search_parent_directories=True).working_dir)


def apps_repo_root() -> Path:
    return APPS_REPO_ROOT
