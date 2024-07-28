from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import re
import requests
from requests import Response, HTTPError


@dataclass
class APOD:
    API_ENDPOINT = 'https://api.nasa.gov/planetary/apod'
    APOD_DATE_FORMATTER = '%Y-%m-%d'
    APOD_DATE_FORMAT = 'YYYY-MM-DD'
    APOD_DATE_FORMAT_RE = r'[0-9]{4}-[0-9]{2}-[0-9]{2}'

    date: str
    title: str
    explanation: str
    url: str
    media_type: str
    hdurl: Optional[str] = field(default=None)
    concepts: Optional[str] = field(default=None)
    thumbnail_url: Optional[str] = field(default=None)
    copyright: Optional[str] = field(default=None)
    resources: Optional[dict] = field(default=None)
    service_version: Optional[str] = field(default=None)

    def _validate_data(self) -> None:
        if not re.match(APOD.APOD_DATE_FORMAT_RE, self.date):
            raise ValueError(f'date must follow format {APOD.APOD_DATE_FORMAT}({APOD.APOD_DATE_FORMAT_RE})')
        if not self.title:
            raise ValueError('APOD must have title')
        if self.url is None and self.hdurl is None:
            raise ValueError('APOD must have at least url or hdurl')

    def __post_init__(self) -> None:
        self._validate_data()

    def __eq__(self, other) -> bool:
        if not isinstance(other, APOD):
            return False
        return self.date == other.date

    @property
    def best_url(self) -> str:
        return self.hdurl or self.url

    @property
    def is_image(self) -> bool:
        return self.media_type == 'image'

    @property
    def datetime(self) -> datetime:
        return datetime(year=int(self.date[0:4]), month=int(self.date[5:7]), day=int(self.date[8:10]))

    @property
    def media_extension(self) -> str:
        ext = self.best_url[self.best_url.rindex('.') + 1:]
        if len(ext) > 4:
            ext = 'jpg'
        return ext

    def __str__(self) -> str:
        return f'{self.date} - {self.media_type} - {self.title}'

    @staticmethod
    def load_from(file: Path) -> APOD:
        with open(file, 'r', encoding='utf-8') as fstream:
            return APOD(**json.loads(fstream.read()))

    @staticmethod
    def fetch_single(api_key: str, date: Optional[str | datetime]) -> APOD:
        if date is None:
            date: datetime = datetime.now()
        if isinstance(date, datetime):
            date: str = date.strftime(APOD.APOD_DATE_FORMATTER)
        if not re.match(APOD.APOD_DATE_FORMAT_RE, date):
            raise ValueError(f'date must follow format {APOD.APOD_DATE_FORMAT}({APOD.APOD_DATE_FORMAT_RE})')

        response: Response = requests.get(APOD.API_ENDPOINT, params={
            'api_key': api_key,
            'date': date
        })

        if not response.ok:
            raise HTTPError(f'HTTP Error, status: {response.status_code}', response=response)

        return APOD(**response.json())

    @staticmethod
    def fetch_random(api_key: str, count: int) -> list[APOD]:
        if not (1 <= count <= 100):
            raise ValueError(f'`count` must be between (0, 100]')

        response: Response = requests.get(APOD.API_ENDPOINT, params={
            'api_key': api_key,
            'count': count
        })

        if not response.ok:
            raise HTTPError(f'HTTP Error, status: {response.status_code}', response=response)

        return [APOD(**data) for data in response.json()]

    @staticmethod
    def fetch_range(api_key: str, start_date: datetime | str, end_date: datetime | str) -> list[APOD]:
        if start_date is None:
            start_date: datetime = datetime.now()
        if isinstance(start_date, datetime):
            start_date: str = start_date.strftime(APOD.APOD_DATE_FORMATTER)
        if not re.match(APOD.APOD_DATE_FORMAT_RE, start_date):
            raise ValueError(f'start_date must follow format {APOD.APOD_DATE_FORMAT}({APOD.APOD_DATE_FORMAT_RE})')

        if end_date is None:
            end_date: datetime = datetime.now()
        if isinstance(end_date, datetime):
            end_date: str = end_date.strftime(APOD.APOD_DATE_FORMATTER)
        if not re.match(APOD.APOD_DATE_FORMAT_RE, end_date):
            raise ValueError(f'end_date must follow format {APOD.APOD_DATE_FORMAT}({APOD.APOD_DATE_FORMAT_RE})')

        response: Response = requests.get(APOD.API_ENDPOINT, params={
            'api_key': api_key,
            'start_date': start_date,
            'end_date': end_date
        })

        if not response.ok:
            raise HTTPError(f'HTTP Error, status: {response.status_code}', response=response)

        return [APOD(**data) for data in response.json()]
