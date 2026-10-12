### Routes for carb calculator function ###

from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from typing import Annotated
from models import NutrientI, NutrientS

router = APIRouter(
    prefix="/carb_counter",
    tags=["carb_counter"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/{food_name}")
def get_carb_value(food_name : str, db : db_dependency):
    response = db.query(NutrientS).filter(NutrientS.food_name == food_name.capitalize()).first()
    if response is None:
        response = db.query(NutrientI).filter(NutrientI.Food_Name == food_name.title()).first()
        if response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return {
            "carbohydrates":str(response.Carbohydrates_g)+" g", 
            "fats":str(response.Fat_g)+" g",
            "calories":str(response.Calories_kcal)+" kcal"
        }
    return {
        "carbohydrates":str(response.carb_g)+" g",
        "fats":str(response.fat_g)+" g",
        "calories":str(response.energy_kcal)+" kcal"
    }