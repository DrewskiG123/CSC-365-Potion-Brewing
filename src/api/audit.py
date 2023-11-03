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
    print("Get Inventory")
    
    pot_count = 0
    with db.engine.begin() as connection:
        gold_sum = connection.execute(sqlalchemy.text("SELECT SUM(gold) FROM global_inventory"))
        gold = gold_sum.scalar_one()    # first()._data[0]

        pots = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM catalog_tracker"))
        pot_count = pots.scalar_one()   # first()._data[0]
        if pot_count == None:
            pot_count = 0
        
        ml_sum = connection.execute(sqlalchemy.text("""
            SELECT SUM(num_red_ml + num_blue_ml + num_green_ml + num_dark_ml) FROM global_inventory"""))
        mils = ml_sum.scalar_one()  # first()._data[0]
        print("gold:", gold, "total pots:", pot_count, "total mls:", mils)
        # print(f"{{\n\tpotions: {pot_count},\n\tred ml: {fr.num_red_ml},\n\tgreen ml: {fr.num_green_ml},\n\tblue ml: {fr.num_blue_ml},\n\tdark ml: {fr.num_dark_ml}\n\tgold: {fr.gold}\n}}")
            
    return {
        "gold": gold,
        "total potions": pot_count,
        "total ml": mils
    }

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
