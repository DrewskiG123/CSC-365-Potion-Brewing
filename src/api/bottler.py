from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ Handling global inventory after bottling """
    print(potions_delivered)

    for pot in potions_delivered:
        if pot.potion_type == ([100, 0, 0, 0]): # if it's a red potion
            with db.engine.begin() as connection:
                red_potions_held = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory WHERE p_key = 0"))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = " + str(red_potions_held + pot.quantity) + " WHERE p_key = 0"))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        red_ml_held = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory WHERE p_key = 0"))
    
    ml_used = 0
    potions_gained = 0

    while red_ml_held > 100: # while I have ml to bottle
        ml_used += 100
        potions_gained += 1
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(red_ml_held - ml_used) + " WHERE p_key = 0") )

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": potions_gained,
            }
        ]
