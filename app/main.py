from typing import Annotated

from fastapi import Depends, FastAPI

from app.config import Settings, get_settings
from app.routers import auth

settings_dep = Annotated[Settings, Depends(get_settings)]
app = FastAPI(title=get_settings().app_name)

app.include_router(auth.router)


@app.get("/", summary="App root")
def read_root(settings: settings_dep):
    return {"message": f"Welcome to the {settings.app_name}"}
