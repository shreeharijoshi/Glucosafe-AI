### Routes for carb calculator function ###

from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, HTTPException
from starlette import status
from typing import Annotated
from models import NutrientI, NutrientS
from sqlalchemy import or_
from rapidfuzz import fuzz, process
import threading

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

LIMIT = 10
FUZZY_CUTOFF = 75         
FUZZY_MIN_QUERY_LEN = 4    

_fuzzy_lock = threading.Lock()
_fuzzy_index = None       

def normalize(s: str) -> str:
    return " ".join(s.casefold().split())


def get_fuzzy_index(db):
    """Build once: casefolded keys (full names + individual words) -> display names."""
    global _fuzzy_index
    if _fuzzy_index is None:
        with _fuzzy_lock:
            if _fuzzy_index is None:
                names = set()
                for col in (NutrientS.food_name_western,
                            NutrientS.food_name_indian,
                            NutrientI.Food_Name):
                    names.update(r[0] for r in db.query(col).filter(col.isnot(None)).all())

                keys, targets = [], []
                for name in names:
                    folded = normalize(name)
                    keys.append(folded)
                    targets.append(name)
                    for word in folded.split():
                        if len(word) >= 3 and word != folded:
                            keys.append(word)
                            targets.append(name)
                _fuzzy_index = (keys, targets)
    return _fuzzy_index


def reset_fuzzy_index():
    """Call after adding or editing foods in the database."""
    global _fuzzy_index
    _fuzzy_index = None


@router.get("/autocomplete")
def suggest_item(
    db: db_dependency,
    food_name: str = Query(..., min_length=3, max_length=50),
):
    term = normalize(food_name)

    s_rows = (
        db.query(NutrientS.food_name_western, NutrientS.food_name_indian)
        .filter(or_(
            NutrientS.food_name_western.contains(term, autoescape=True),
            NutrientS.food_name_indian.contains(term, autoescape=True),
        ))
        .all()
    )
    i_rows = (
        db.query(NutrientI.Food_Name)
        .filter(NutrientI.Food_Name.contains(term, autoescape=True))
        .all()
    )

    raw_names = [n for row in s_rows for n in row] + [r[0] for r in i_rows]

    ranked, seen = [], set()
    for name in raw_names:
        if not name:
            continue
        folded = normalize(name)
        if folded in seen or term not in folded:
            continue
        seen.add(folded)
        if folded.startswith(term):
            tier = 0
        elif f" {term}" in f" {folded}":
            tier = 1
        else:
            tier = 2
        ranked.append((tier, len(folded), folded, name))
    ranked.sort()

    results = [{"name": name, "match_type": "exact"} for *_, name in ranked]
    has_strong_match = any(tier < 2 for tier, *_ in ranked)

    if not has_strong_match and len(term) >= FUZZY_MIN_QUERY_LEN:
        keys, targets = get_fuzzy_index(db)
        hits = process.extract(
            term, keys,
            scorer=fuzz.ratio,
            score_cutoff=FUZZY_CUTOFF,
            limit=LIMIT * 3,       
        )
        for _key, score, idx in hits:
            name = targets[idx]
            folded = normalize(name)
            if folded in seen:
                continue
            seen.add(folded)
            results.append({
                "name": name,
                "match_type": "fuzzy",
                "confidence": round(score, 1),
            })

    return results[:LIMIT]

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