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

    red_potions_held = -1 # if this is returned something is wrong
    amnt = 0

    for pot in potions_delivered:
        if pot.potion_type[0] == 100: # if it's a red potion
            print("made it in\n")
            with db.engine.begin() as connection:
                result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
                # result.first() is the first row of global_inventory
                red_potions_held = result.first().num_red_potions
                amnt = pot.quantity
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = " + str(red_potions_held + pot.quantity) + " WHERE p_key = 0"))

    return "OK", red_potions_held+amnt, "^ new potion #"

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

    red_ml_held = -1
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # result.first() is the first row of global_inventory
        red_ml_held = result.first().num_red_ml
    
    potions_gained = 0

    while red_ml_held > 100: # while I have ml to bottle
        potions_gained += 1
        red_ml_held -= 100

    if potions_gained > 0:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(red_ml_held) + " WHERE p_key = 0") )
        
        return [
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": potions_gained,
                }
            ]
    else:
        return []
