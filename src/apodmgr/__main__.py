from sys import argv
from typing import Callable, Optional
from dataclasses import asdict
from pathlib import Path
from datetime import datetime
import re
import json
from .apod import APOD
from .mgrcfg import ManagerConfiguration, default_manager_configuration_path
from .set_bg import set_bg


def int_or_none(string: str) -> Optional[int]:
    try:
        return int(string)
    except ValueError:
        return None


FETCH_HELP_MSG = f"""
Must specify either:
<date: {APOD.APOD_DATE_FORMAT}>
<count: int>
<start_date: {APOD.APOD_DATE_FORMAT}> <end_date: {APOD.APOD_DATE_FORMAT}>'
today
"""


def fetch(config: ManagerConfiguration):
    if not argv:
        print(FETCH_HELP_MSG)
        return
    if len(argv) == 1:
        if re.match(APOD.APOD_DATE_FORMAT_RE, argv[0]):
            fetcher: Callable = lambda: config.fetch_single(argv[0])
        elif (count := int_or_none(argv[0])) is not None:
            fetcher: Callable = lambda: config.fetch_random(count)
        elif argv[0] == 'today':
            fetcher: Callable = lambda: config.fetch_single(None)
        else:
            print(FETCH_HELP_MSG)
            return
        argv.pop(0)
    elif re.match(APOD.APOD_DATE_FORMAT_RE, argv[0]) and re.match(APOD.APOD_DATE_FORMAT_RE, argv[1]):
        fetcher: Callable = lambda: config.fetch_range(argv[0], argv[1])
        argv.pop(0)
        argv.pop(0)
    else:
        print(FETCH_HELP_MSG)
        return

    apods: list[APOD] | APOD = fetcher()
    if isinstance(apods, APOD):
        apods: list[APOD] = [apods]

    for apod in apods:
        print(apod)


def list_apods(config: ManagerConfiguration):
    for apod_file_name in config.stored_apods():
        apod = APOD.load_from(Path(config.apods_path) / apod_file_name)
        print(apod)


DOWNLOAD_MEDIA_HELP_MSG = f"""
Must specify either:
<date: {APOD.APOD_DATE_FORMAT}>
today
"""


def download_media(config: ManagerConfiguration):
    if not argv:
        print(DOWNLOAD_MEDIA_HELP_MSG)
        return
    date: str = argv.pop(0)
    if date == 'today':
        date: str = datetime.now().strftime(APOD.APOD_DATE_FORMATTER)
    file_name: str = f'{date}.json'
    if file_name not in config.stored_apods():
        print(f'Haven\'t fetched {date} yet...')
        return
    apod = config.fetch_single(date)
    config.save_media_for(apod)
    print(Path(config.apods_media_path) / f'{apod.date}.{apod.media_extension}')


def set_background(config: ManagerConfiguration):
    if not argv:
        print(DOWNLOAD_MEDIA_HELP_MSG)
        return
    date: str = argv.pop(0)
    if date == 'today':
        date: str = datetime.now().strftime(APOD.APOD_DATE_FORMATTER)
    if (apod_file_name := config.stored_apod_file(date)) is None:
        print(f'Haven\'t fetched {date} yet...')
        return
    media_path: Path = config.path_for_media(APOD.load_from(Path(config.apods_path) / apod_file_name))
    if not media_path.exists():
        print(f'Haven\'t downloaded media for {date} yet...')
        return
    set_bg(media_path)
    print(media_path)


def mkcfg():
    path = default_manager_configuration_path()
    if path.exists():
        if input(f'Configuration {path} already exists, overwrite? (Y/n)') != 'Y':
            return

    if not path.parent.exists():
        path.parent.mkdir()

    with open(str(path), 'w', encoding='utf-8') as fstream:
        fstream.write(json.dumps(asdict(ManagerConfiguration('')), indent=4))
    print(f'Configuration created in {path}')


def main():
    argv.pop(0)
    if not argv:
        print('Must specify a command')
        return
    command = argv.pop(0)

    no_cfg_commands: dict[str, Callable] = {
        'mkcfg': mkcfg
    }

    if command in no_cfg_commands:
        no_cfg_commands[command]()
        return

    if not default_manager_configuration_path().exists():
        print(f'{default_manager_configuration_path()} not found')
        return

    config: ManagerConfiguration = ManagerConfiguration.load_from(default_manager_configuration_path())

    commands: dict[str, Callable[[ManagerConfiguration], None]] = {
        'fetch': fetch,
        'list': list_apods,
        'download': download_media,
        'set-bg': set_background
    }

    if command not in commands:
        print(f'Must specify a valid command:')
        for command in no_cfg_commands:
            print(command)
        for command in commands:
            print(command)
        return

    commands[command](config)


if __name__ == '__main__':
    main()
