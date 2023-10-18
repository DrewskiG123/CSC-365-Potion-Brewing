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
    inv_lst = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT name, sku, potion_type, inventory FROM potions"))
        for name, sku, potion_type, inventory in result:
            print(f"{{\n\tname: {name},\n\tsku: {sku},\n\ttype: {potion_type},\n\tinventory: {inventory}\n}}")
            inv_lst.append({
                "name": name, 
                "sku": sku, 
                "type": potion_type, 
                "inventory": inventory})
        
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        fr = result.first()
        print(f"{{\n\tred ml: {fr.num_red_ml},\n\tgreen ml: {fr.num_green_ml},\n\tblue ml: {fr.num_blue_ml},\n\tdark ml: {fr.num_dark_ml}\n\tgold: {fr.gold}\n}}")
        inv_lst.append({
            "red ml": fr.num_red_ml, 
            "green ml": fr.num_green_ml, 
            "blue ml": fr.num_blue_ml, 
            "dark ml": fr.num_dark_ml, 
            "gold": fr.gold})

    return inv_lst

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
