import logging.config

import yaml

# Must precede any imports, see https://stackoverflow.com/a/20280587.
with open("logging.yaml", "r") as file:
    log_settings = yaml.safe_load(file.read())
    logging.config.dictConfig(log_settings)


def main():
    pass


if __name__ == "__main__":
    main()
