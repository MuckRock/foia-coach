# settings to run on Render
from .base import *

import dj_database_url

DATABASES = {
    "default": dj_database_url.parse(
        "postgres://...",
        conn_max_age=600,
        conn_health_checks=True,
    )
}
