### Routes for carb calculator function ###

from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, HTTPException
from starlette import status
from typing import Annotated
from models import NutrientI, NutrientS
from sqlalchemy import or_

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

@router.get("/autocomplete")
def suggest_item(db : db_dependency, food_name : str = Query(minlength=3)):
    search_term = food_name.casefold()
    response = set()

    nutrient_s_results = db.query(NutrientS).filter(
        or_(
            NutrientS.food_name_western.contains(search_term),
            NutrientS.food_name_indian.contains(search_term)
        )
    ).all()

    nutrient_i_results = db.query(NutrientI).filter(NutrientI.Food_Name.contains(search_term)).all()

    for item in nutrient_s_results:
        if item.food_name_western and search_term in item.food_name_western.casefold():
            response.add(item.food_name_western)
        if item.food_name_indian and search_term in item.food_name_indian.casefold():
            response.add(item.food_name_indian)
        
    for item in nutrient_i_results:
        if item.Food_Name and search_term in item.Food_Name.casefold():
            response.add(item.Food_Name)
        
    return list(response)

@router.get("/{food_name}")
def get_carb_value(food_name : str, db : db_dependency):
    response = db.query(NutrientS).filter(NutrientS.food_name_western == food_name.capitalize()).first()
    if response is None:
        response = db.query(NutrientS).filter(NutrientS.food_name_indian == food_name.capitalize()).first()
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