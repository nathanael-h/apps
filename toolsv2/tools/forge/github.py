#!/usr/bin/env python3

import logging
from functools import cache

import github

from ..utils.paths import APPS_REPO_ROOT


@cache
def github_login() -> str | None:
    if (file := APPS_REPO_ROOT / ".github_login").exists():
        return file.open(encoding="utf-8").read().strip()
    return None


@cache
def github_email() -> str | None:
    if (file := APPS_REPO_ROOT / ".github_email").exists():
        return file.open(encoding="utf-8").read().strip()
    return None


@cache
def github_token() -> str | None:
    if (file := APPS_REPO_ROOT / ".github_token").exists():
        return file.open(encoding="utf-8").read().strip()
    return None


@cache
def github_auth() -> github.Auth.Auth | None:
    token = github_token()
    if token is None:
        logging.warning("Could not get Github token authentication.")
        return None
    return github.Auth.Token(token)


@cache
def github_api() -> github.Github:
    auth = github_auth()
    if auth is None:
        logging.warning("Returning unauthenticated Github API.")
        return github.Github()
    return github.Github(auth=auth)
