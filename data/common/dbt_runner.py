import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from common.secrets_retriever import fetch_secret

DBT_DIR = Path(__file__).parents[1] / "topdeck_dbt"


def main() -> None:
    dsn = urlsplit(fetch_secret("topdeck-db-dsn"))

    os.environ["TOPDECK_DB_HOST"] = dsn.hostname or ""
    os.environ["TOPDECK_DB_USER"] = dsn.username or ""
    os.environ["TOPDECK_DB_PASSWORD"] = dsn.password or ""

    result = subprocess.run(["dbt", "build"], cwd=DBT_DIR)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
