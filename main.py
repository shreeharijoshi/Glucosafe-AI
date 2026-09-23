### Entry file ###

from fastapi import FastAPI, APIRouter
from routers import carb_count
from starlette import status

app = FastAPI()

@app.get("/healthy", status_code=status.HTTP_200_OK)
def test_health():
    return {"status":"healthy"}

app.include_router(carb_count.router)
