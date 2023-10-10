from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ Returns the current shop inventory """
    # these should NOT get returned
    red_potions_held = -1
    red_ml_held = -1

    green_potions_held = -1
    green_ml_held = -1

    blue_potions_held = -1
    blue_ml_held = -1

    gold_held = -1

    with db.engine.begin() as connection:
        print("inside \"with\" section\n")
        # result.first() is the first row of global_inventory
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        fr = result.first()
        
        red_potions_held = fr.num_red_potions
        red_ml_held = fr.num_red_ml

        green_potions_held = fr.num_green_potions
        green_ml_held = fr.num_green_ml

        blue_potions_held = fr.num_blue_potions
        blue_ml_held = fr.num_blue_ml

        gold_held = fr.gold
    
    return [
        {"number_of_red_potions": red_potions_held, "ml_in_barrels": red_ml_held},
        {"number_of_green_potions": green_potions_held, "ml_in_barrels": green_ml_held},
        {"number_of_blue_potions": blue_potions_held, "ml_in_barrels": blue_ml_held},
        {"gold": gold_held}]

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ Displays audit results """
    print(audit_explanation)

    return "OK"
