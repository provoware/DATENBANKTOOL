"""Start über ``python -m datenbanktool``."""

from .cli import main

from datenbanktool.entrypoint import main

raise SystemExit(main())
