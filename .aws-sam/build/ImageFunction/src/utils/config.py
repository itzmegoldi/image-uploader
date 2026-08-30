import os
import re
from typing import Any, Optional

import yaml
from pydantic import TypeAdapter
from typing_extensions import Self

ENV_PATTERN = r'\$env\["([^"]+)"\]'


class ConfigException(Exception):
    pass


class EnvNotSetException(ConfigException):
    pass


def process_yaml_data(data: Any, strict: bool = True):
    if isinstance(data, dict):
        for key, value in data.items():  # type: ignore
            if isinstance(value, str) and value.startswith("$"):
                ok, _, env_value = get_env_key_value(
                    pattern=ENV_PATTERN,
                    value=value,
                    strict=strict,
                )
                if not ok:
                    continue
                data[key] = env_value
            elif isinstance(value, (dict, list)):
                process_yaml_data(value, strict)
    elif isinstance(data, list):
        for value in data:  # type: ignore
            process_yaml_data(value, strict)


def get_env_key_value(
    pattern: str, value: str, strict: bool = True
) -> tuple[bool, str, Optional[str]]:
    match = re.match(pattern, value)
    if not match:
        return (False, "", None)
    env_key = match.group(1)
    env_value = os.environ.get(env_key, "$$null")
    if strict and env_value == "$$null":
        raise EnvNotSetException(f"{env_key} not set")
    if not strict and env_value == "$$null":
        env_value = value

    return True, env_key, env_value


def recursive_merge(original: Any, to_merge: Any) -> Any:
    for key, value in to_merge.items():
        if key in original:
            if isinstance(original[key], list) and isinstance(value, list):
                original[key].extend(value)
            elif isinstance(original[key], dict) and isinstance(value, dict):
                original[key] = recursive_merge(original[key], value)
            else:
                original[key] = value
        else:
            original[key] = value
    return original


def load_and_merge_from_yaml(config_dir: str, environment: str, strict: bool = True):
    all_data: Any = []
    for env_name in [environment]:
        file_name = os.path.join(config_dir, f"{env_name}.yaml")
        if not os.path.isfile(file_name):
            continue
        with open(file_name, "rb") as file:
            data = yaml.safe_load(file)
        process_yaml_data(data, False)
        all_data.append(data)

    if len(all_data) == 2:
        merged_data = recursive_merge(all_data[0], all_data[0])
    else:
        merged_data = all_data[0]

    process_yaml_data(merged_data, strict=strict)
    return merged_data


class ConfigMixIn:

    @classmethod
    def from_yaml(cls, config_dir: str, env_name: str, strict: bool = True) -> Self:
        merged_data = load_and_merge_from_yaml(
            config_dir=config_dir, environment=env_name, strict=strict
        )
        ta = TypeAdapter(cls)
        return ta.validate_python(merged_data)
