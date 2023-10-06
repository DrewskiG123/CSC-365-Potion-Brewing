from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ Handles barrel reception (updating ml and gold) """
    
    print(barrels_delivered)
    
    gold_held = -1
    red_ml_held = -1
    cost = 0
    ml_added = 0

    for barrel in barrels_delivered:
        if barrel.quantity > 0 and barrel.sku == "SMALL_RED_BARREL":
            cost += (barrel.price)
            ml_added += (barrel.ml_per_barrel)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = result.first()
        gold_held = fr.gold
        red_ml_held = fr.num_red_ml
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(gold_held - cost) 
                                           + ", num_red_ml = " + str(red_ml_held + ml_added) + " WHERE id = 0"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ Returns what barrels to purchase to keep stocks up """

    print(wholesale_catalog)

    gold_held = -1
    red_potions_held = -1
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = result.first()
        gold_held = fr.gold
        red_potions_held = fr.num_red_potions

    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL" and barrel.price < gold_held:
            if red_potions_held < 10:
                return [
                    {
                        "sku": "SMALL_RED_BARREL",
                        "quantity": 1,
                    }
                ]
            else:
                return []
