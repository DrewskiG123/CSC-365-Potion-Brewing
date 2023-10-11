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

    r_pots = 0
    g_pots = 0
    b_pots = 0

    for pot in potions_delivered:
        if pot.potion_type[0] == 100: # if it's a red potion
            r_pots = pot.quantity
        if pot.potion_type[1] == 100: # if it's a green potion
            g_pots = pot.quantity
        if pot.potion_type[2] == 100: # if it's a blue potion
            b_pots = pot.quantity
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_red_ml = num_red_ml - " + str(r_pots*100) + ",\n"+
            "   num_green_ml = num_green_ml - " + str(g_pots*100) + ",\n"+
            "   num_blue_ml = num_blue_ml - " + str(b_pots*100) + ",\n"+
            "   num_red_potions = num_red_potions + " + str(r_pots) + ",\n"+
            "   num_green_potions = num_green_potions + " + str(g_pots) + ",\n"+
            "   num_blue_potions = num_blue_potions + " + str(b_pots) + " WHERE id = 0") )

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    Each bottle has a quantity of what proportion of red, blue, and
    green potion to add.
    Expressed in integers from 1 to 100 that must sum up to 100.
    Initial logic: bottle all barrels into red potions.
    """
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    # Initial logic: bottle all barrels into red potions.

    r_ml_held = -1
    g_ml_held = -1
    b_ml_held = -1
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = result.first()
        r_ml_held = fr.num_red_ml
        g_ml_held = fr.num_green_ml
        b_ml_held = fr.num_blue_ml
    
    r_potions_gained = 0
    g_potions_gained = 0
    b_potions_gained = 0

    bottle_lst = [] # bottles of potions

    while r_ml_held >= 100: # while I have red ml to bottle
        r_potions_gained += 1
        r_ml_held -= 100
    
    if r_potions_gained > 0:
        bottle_lst.append({"potion_type": [100, 0, 0, 0], "quantity": r_potions_gained})
    
    while g_ml_held >= 100: # while I have green ml to bottle
        g_potions_gained += 1
        g_ml_held -= 100

    if g_potions_gained > 0:
        bottle_lst.append({"potion_type": [0, 100, 0, 0], "quantity": g_potions_gained})
    
    while b_ml_held >= 100: # while I have blue ml to bottle
        b_potions_gained += 1
        b_ml_held -= 100
    
    if b_potions_gained > 0:
        bottle_lst.append({"potion_type": [0, 0, 100, 0], "quantity": b_potions_gained})
    
    return bottle_lst
