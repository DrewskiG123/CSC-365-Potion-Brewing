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
    
    cost = 0
    ml_added = 0

    for barrel in barrels_delivered:
        if barrel.quantity > 0 and barrel.sku == "SMALL_RED_BARREL":
            cost += (barrel.price)
            ml_added += (barrel.ml_per_barrel)

    with db.engine.begin() as connection:
        gold_held = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        red_ml_held = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(gold_held - cost) 
                                                                + ", num_red_ml = " + str(red_ml_held + ml_added) ) )

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ Returns what barrels to purchase to keep stocks up """

    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        gold_held = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        red_potions_held = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))

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
                return [
                    {
                        "sku": "SMALL_RED_BARREL",
                        "quantity": 0,
                    }
                ]