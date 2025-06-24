"""A class to hold entity values."""

from __future__ import annotations

import fnmatch
from functools import lru_cache
import re
from typing import Any

from homeassistant.const import MAX_EXPECTED_ENTITY_IDS
from homeassistant.core import split_entity_id


class EntityValues:
    """Class to store entity id based values.

    This class is expected to only be used infrequently
    as it caches all entity ids up to MAX_EXPECTED_ENTITY_IDS.

    The cache includes `self` so it is important to
    only use this in places where usage of `EntityValues` is immortal.
    """

    def __init__(
        self,
        exact: dict[str, dict[str, str]] | None = None,
        domain: dict[str, dict[str, str]] | None = None,
        glob: dict[str, dict[str, str]] | None = None,
    ) -> None:
        """
        Initialize an EntityValues instance with optional exact, domain, and glob pattern configuration mappings.
        
        Parameters:
            exact: Optional mapping of exact entity IDs to their configuration dictionaries.
            domain: Optional mapping of domains to their configuration dictionaries.
            glob: Optional mapping of glob-style string patterns to their configuration dictionaries.
        """
        self._exact = exact
        self._domain = domain

        if glob is None:
            compiled: dict[re.Pattern[str], Any] | None = None
        else:
            compiled = {
                re.compile(fnmatch.translate(key)): value for key, value in glob.items()
            }

        self._glob = compiled

    @lru_cache(maxsize=4096)
    def get(self, entity_id: str) -> dict[str, str]:
        """
        Retrieve the aggregated configuration dictionary for a given entity ID.
        
        The method combines configuration values from exact entity ID matches, domain-based matches, and glob pattern matches, with later matches overriding earlier ones if keys overlap.
        
        Parameters:
            entity_id (str): The entity ID for which to retrieve configuration.
        
        Returns:
            dict[str, str]: The combined configuration dictionary for the specified entity ID.
        """
        domain, _ = split_entity_id(entity_id)
        result: dict[str, str] = {}

        if self._domain is not None and domain in self._domain:
            result.update(self._domain[domain])

        if self._glob is not None:
            for pattern, values in self._glob.items():
                if pattern.match(entity_id):
                    result.update(values)

        if self._exact is not None and entity_id in self._exact:
            result.update(self._exact[entity_id])

        return result
