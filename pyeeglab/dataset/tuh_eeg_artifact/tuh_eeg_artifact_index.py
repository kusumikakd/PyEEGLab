import logging
import re
import json

from typing import List

from uuid import uuid4, uuid5, NAMESPACE_X500
from os.path import join, sep

from ...io import Index, Raw
from ...database import File, Metadata, Event


class TUHEEGArtifactIndex(Index):

    def __init__(self, path: str) -> None:
        logging.debug('Create TUH EEG Corpus Index')
        super().__init__('sqlite:///' + join(path, 'index.db'), path)
        self.index()

    def _get_file(self, path: str) -> File:
        length = len(self.path)
        meta = path[length:].split(sep)
        return File(
            id=str(uuid5(NAMESPACE_X500, path[length:])),
            extension=meta[-1].split('.')[-1],
            path=path[length:]
        )

    def _get_record_metadata(self, file: File) -> Metadata:
        logging.debug('Add file %s raw metadata to index', file.id)
        meta = file.path.split(sep)
        raw = Raw(file.id, join(self.path, file.path))
        return Metadata(
            file_id=raw.id,
            file_duration=raw.open().n_times/raw.open().info['sfreq'],
            channels_count=raw.open().info['nchan'],
            channels_reference=meta[0],
            channels_set=json.dumps(raw.open().info['ch_names']),
            sampling_frequency=raw.open().info['sfreq'],
            max_value=raw.open().get_data().max(),
            min_value=raw.open().get_data().min(),
        )

    def _get_record_events(self, file: File) -> List[Event]:
        logging.debug('Add file %s raw events to index', file.id)
        raw = Raw(file.id, join(self.path, file.path))
        path = raw.path[:-4] + '.tse'
        with open(path, 'r') as file:
            annotations = file.read()
        pattern = re.compile(
            r'^(\d+.\d+) (\d+.\d+) (\w+) (\d.\d+)$', re.MULTILINE)
        events = re.findall(pattern, annotations)
        events = [
            Event(
                id=str(uuid4()),
                file_id=raw.id,
                begin=float(event[0]),
                end=float(event[1]),
                duration=(float(event[1])-float(event[0])),
                label=event[2]
            )
            for event in events
        ]
        return events
