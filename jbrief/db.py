from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

TORTOISE_ORM = {
    "connections": {"default": "sqlite:///Users/freddy.boulton/sources/py-jbrief-api/jbrief.sqlite3"},
    "apps": {
        "models": {
            "models": ["jbrief.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


def init_db(app: FastAPI) -> None:
    register_tortoise(
        app,
        db_url=TORTOISE_ORM["connections"]["default"],
        modules={"models": ["jbrief.models"]},
        generate_schemas=False,
        add_exception_handlers=True,
    )