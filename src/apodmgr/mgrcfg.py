from __future__ import annotations
from typing import Optional
from os import listdir
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
import json
import os
import re
from .apod import APOD
import requests
from requests import Response, HTTPError


def default_apods_dir() -> str:
    return str(Path.home() / Path('Pictures' if os.name == 'nt' else '') / 'apods')


def default_apods_media_dir() -> str:
    return str(Path.home() / Path('Pictures' if os.name == 'nt' else '') / 'apods' / 'images')


def default_manager_configuration_path() -> Path:
    return Path(default_apods_dir()) / "apodmgr.cfg.json"


@dataclass
class ManagerConfiguration:
    api_key: str
    apods_path: str = field(default_factory=default_apods_dir)
    apods_media_path: str = field(default_factory=default_apods_media_dir)

    def _validate_data(self) -> ManagerConfiguration:
        if self.api_key.strip() == '':
            raise ValueError(f'API key must not be blank')
        if not Path(self.apods_path).exists():
            Path(self.apods_path).mkdir()
        if not Path(self.apods_media_path).exists():
            Path(self.apods_media_path).mkdir()
        return self

    @staticmethod
    def load_from(file: Path):
        if not file.is_file():
            raise FileNotFoundError(f'Cannot load {ManagerConfiguration} from {file}')
        with open(file, 'r', encoding='utf-8') as file:
            data: dict[str, str] = json.loads(file.read())
        if 'api_key' not in data:
            raise ValueError(f'{ManagerConfiguration} file {file} does not contain required `api_key`')
        return ManagerConfiguration(**data)._validate_data()

    def store_apod(self, apod: APOD) -> APOD:
        with open(Path(self.apods_path) / f'{apod.date}.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(asdict(apod), indent=4))
        return apod

    def store_apods(self, apods: list[APOD]) -> list[APOD]:
        for apod in apods:
            self.store_apod(apod)
        return apods

    def stored_apods(self):
        file_name_pattern: str = f'{APOD.APOD_DATE_FORMAT_RE}.json'
        for file in listdir(self.apods_path):
            if re.match(file_name_pattern, file):
                yield file

    def stored_media(self):
        file_name_pattern: str = f'{APOD.APOD_DATE_FORMAT_RE}.(jpg|png|mp4)'
        for file in listdir(self.apods_path):
            if re.match(file_name_pattern, file):
                yield file

    def stored_apod_file(self, date: str | datetime) -> str | None:
        if isinstance(date, datetime):
            date: str = date.strftime(APOD.APOD_DATE_FORMATTER)
        if not re.match(APOD.APOD_DATE_FORMAT_RE, date):
            raise ValueError(f'date must follow format {APOD.APOD_DATE_FORMAT}({APOD.APOD_DATE_FORMAT_RE})')
        file_name: str = f'{date}.json'
        for file in listdir(self.apods_path):
            if file_name == file:
                return file
        return None

    def fetch_single(self, date: Optional[str | datetime]) -> APOD:
        if date is not None and (file_name := self.stored_apod_file(date)) is not None:
            with open(Path(self.apods_path) / file_name, 'r', encoding='utf-8') as fstream:
                return APOD(**json.loads(fstream.read()))
        return self.store_apod(APOD.fetch_single(self.api_key, date))

    def fetch_random(self, *args) -> list[APOD]:
        return self.store_apods(APOD.fetch_random(self.api_key, *args))

    def fetch_range(self, *args) -> list[APOD]:
        return self.store_apods(APOD.fetch_range(self.api_key, *args))

    def save_media_for(self, apod: APOD) -> None:
        file_name: str = f'{apod.date}.{apod.media_extension}'
        for file in listdir(self.apods_media_path):
            if file_name == file:
                return

        if not apod.is_image:
            raise TypeError(f'{apod} is not a savable image')
        response: Response = requests.get(apod.best_url)
        if not response.ok:
            raise HTTPError(f'HTTP Error, status: {response.status_code}', response=response)

        with open(Path(self.apods_media_path) / file_name, 'wb') as media:
            media.write(response.content)
