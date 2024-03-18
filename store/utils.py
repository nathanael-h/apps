#!/usr/bin/env python3

import base64
import json
import os
import subprocess
import time
from hashlib import md5
from pathlib import Path

import pycmarkgfm
import tomlkit
from emoji import emojize
from flask import request

TRANSLATIONS_DIR = Path(__file__).parent / "translations"


AVAILABLE_LANGUAGES = ["en"] + [str(d) for d in TRANSLATIONS_DIR.glob("*/")]


def get_locale():
    # try to guess the language from the user accept
    # The best match wins.
    return request.accept_languages.best_match(AVAILABLE_LANGUAGES) or "en"


def get_catalog():
    path = Path("../builds/default/v3/apps.json").resolve()

    mtime = path.stat().st_mtime
    if get_catalog.mtime_catalog != mtime:
        get_catalog.mtime_catalog = mtime

        catalog = json.load(path.open())
        catalog["categories"] = {c["id"]: c for c in catalog["categories"]}
        catalog["antifeatures"] = {c["id"]: c for c in catalog["antifeatures"]}

        category_color = {
            "synchronization": "sky",
            "publishing": "yellow",
            "communication": "amber",
            "office": "lime",
            "productivity_and_management": "purple",
            "small_utilities": "black",
            "reading": "emerald",
            "multimedia": "fuchsia",
            "social_media": "rose",
            "games": "violet",
            "dev": "stone",
            "system_tools": "black",
            "iot": "orange",
            "wat": "teal",
        }

        for id_, category in catalog["categories"].items():
            category["color"] = category_color[id_]

        get_catalog.cache_catalog = catalog

    return get_catalog.cache_catalog


get_catalog.mtime_catalog = None
get_catalog()


def get_wishlist():
    path = Path("../wishlist.toml").resolve()
    mtime = path.stat().st_mtime
    if get_wishlist.mtime_wishlist != mtime:
        get_wishlist.mtime_wishlist = mtime
        get_wishlist.cache_wishlist = tomlkit.load(path.open())

    return get_wishlist.cache_wishlist


get_wishlist.mtime_wishlist = None
get_wishlist()


def get_stars():
    checksum = (
        subprocess.check_output("find . -type f -printf '%T@,' | md5sum", shell=True)
        .decode()
        .split()[0]
    )
    if get_stars.cache_checksum != checksum:
        stars = {}
        for folder, _, files in os.walk(".stars/"):
            app_id = folder.split("/")[-1]
            if not app_id:
                continue
            stars[app_id] = set(files)
        get_stars.cache_stars = stars
        get_stars.cache_checksum = checksum

    return get_stars.cache_stars


get_stars.cache_checksum = None
get_stars()


def check_wishlist_submit_ratelimit(user):

    dir_ = Path(".wishlist_ratelimit").resolve()
    dir_.mkdir(exist_ok=True)
    f = dir_ / md5(user.encode()).hexdigest()

    return not f.exists() or (time.time() - f.stat().st_mtime) > (
        15 * 24 * 3600
    )  # 15 days


def save_wishlist_submit_for_ratelimit(user):

    dir_ = Path(".wishlist_ratelimit").resolve()
    dir_.mkdir(exist_ok=True)

    f = dir_ / md5(user.encode()).hexdigest()
    f.touch()


def human_to_binary(size: str) -> int:
    symbols = ("K", "M", "G", "T", "P", "E", "Z", "Y")
    factor = {}
    for i, s in enumerate(symbols):
        factor[s] = 1 << (i + 1) * 10

    suffix = size[-1]
    size = size[:-1]

    if suffix not in symbols:
        raise Exception(f"Invalid size suffix '{suffix}', expected one of {symbols}")

    try:
        size_ = float(size)
    except Exception:
        raise Exception(f"Failed to convert size {size} to float")  # noqa: B904

    return int(size_ * factor[suffix])


def get_app_md_and_screenshots(app_folder, infos):
    locale = get_locale()

    description_path_localized = app_folder / "doc" / f"DESCRIPTION_{locale}.md"
    description_path_generic = app_folder / "doc" / "DESCRIPTION.md"

    if locale != "en" and description_path_localized.exists():
        description_path = description_path_localized
    elif description_path_generic.exists():
        description_path = description_path_generic
    else:
        description_path = None
    if description_path:
        with description_path.open() as f:
            infos["full_description_html"] = emojize(
                pycmarkgfm.gfm_to_html(f.read()), language="alias"
            )
    else:
        infos["full_description_html"] = infos["manifest"]["description"][locale]

    preinstall_path_localized = app_folder / "doc" / f"PRE_INSTALL_{locale}.md"
    preinstall_path_generic = app_folder / "doc" / "PRE_INSTALL.md"

    if locale != "en" and preinstall_path_localized.exists():
        pre_install_path = preinstall_path_localized
    elif preinstall_path_generic.exists():
        pre_install_path = preinstall_path_generic
    else:
        pre_install_path = None
    if pre_install_path:
        with pre_install_path.open() as f:
            infos["pre_install_html"] = emojize(
                pycmarkgfm.gfm_to_html(f.read()), language="alias"
            )

    infos["screenshot"] = None

    screenshots_folder = app_folder / "doc" / "screenshots"

    if screenshots_folder.exists():
        with screenshots_folder.iterdir() as it:
            for entry in it:
                ext = entry.suffix.lower()
                if entry.is_file() and ext in ("png", "jpg", "jpeg", "webp", "gif"):
                    with entry.open("rb") as img_file:
                        data = base64.b64encode(img_file.read()).decode("utf-8")
                        infos["screenshot"] = (
                            f"data:image/{ext};charset=utf-8;base64,{data}"
                        )
                    break

    ram_build_requirement = infos["manifest"]["integration"]["ram"]["build"]
    infos["manifest"]["integration"]["ram"]["build_binary"] = human_to_binary(
        ram_build_requirement
    )
