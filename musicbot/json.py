import json
import pathlib
import logging
from typing import Any, Dict

log = logging.getLogger(__name__)


class Json:
    def __init__(self, json_file: pathlib.Path) -> None:
        log.debug("Init JSON obj with {0}".format(json_file))
        self.file = json_file
        self.data = self.parse()

    def parse(self) -> Dict[str, Any]:
        """Parse the file as JSON"""
        parsed = {}
        with open(self.file, encoding="utf-8") as data:
            try:
                parsed = json.load(data)
                if type(parsed) is not dict:
                    raise TypeError("Parsed information must be of type Dict[str, Any]")
            except Exception:
                log.error("Error parsing {0} as JSON".format(self.file), exc_info=True)
                parsed = {}
        return parsed

    def get(self, item: str , fallback: Any = None) -> Any:
        """Gets an item from a JSON file"""
        try:
            data = self.data[item]
        except KeyError:
            log.warning("Could not grab data from JSON key {0}.".format(item))
            data = fallback
        return data


class I18nJson(Json):
    def get(self, item: str, fallback: Any = None) -> Any:
        try:
            data = self.data[item]
        except KeyError:
            log.warning(f"Could not grab data from i18n key {item}.")
            data = fallback
        return data
