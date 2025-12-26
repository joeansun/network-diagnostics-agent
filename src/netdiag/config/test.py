import tomllib

from loader import ensure_config_file

file = ensure_config_file()
with file.open("rb") as f:
    data = tomllib.load(f)
print(data)