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
    d_pots = 0
    # custom pots
    p_pots = 0

    for pot in potions_delivered:
        match pot.potion_type:
            case [100,0,0,0]:# if it's a red potion
                r_pots = pot.quantity
            case [0,100,0,0]:# if it's a green potion
                g_pots = pot.quantity
            case [0,0,100,0]:# if it's a blue potion
                b_pots = pot.quantity
            case [0,0,0,100]:# if it's a dark potion
                d_pots = pot.quantity
            case [50,0,50,0]:# if it's a purple potion
                p_pots = pot.quantity
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
        """ UPDATE global_inventory 
            SET num_red_ml = num_red_ml - :r_mls - :p_mls,
                num_green_ml = num_green_ml - :g_mls,
                num_blue_ml = num_blue_ml - :b_mls - :p_mls,
                num_dark_ml = num_dark_ml - :d_mls
            WHERE id = 0;
            
            UPDATE catalog
            SET inventory = 
                CASE id
                    WHEN 1 THEN inventory + :r_pots
                    WHEN 2 THEN inventory + :g_pots
                    WHEN 3 THEN inventory + :b_pots
                    WHEN 4 THEN inventory + :d_pots
                    WHEN 5 THEN inventory + :p_pots
                END
            WHERE  id IN (1, 2, 3, 4, 5);
        """), [{"r_mls": r_pots*100, "g_mls": g_pots*100, "b_mls": b_pots*100, "d_mls": d_pots*100, "p_mls": p_pots*50, 
                "r_pots": r_pots, "g_pots": g_pots, "b_pots": b_pots, "d_pots": d_pots, "p_pots": p_pots}])

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
    d_ml_held = -1

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = result.first()
        r_ml_held = fr.num_red_ml
        g_ml_held = fr.num_green_ml
        b_ml_held = fr.num_blue_ml
        d_ml_held = fr.num_dark_ml
    
    r_potions_gained = 0
    g_potions_gained = 0
    b_potions_gained = 0
    d_potions_gained = 0

    # custom colors (just purple for now)
    p_potions_gained = 0

    bottle_lst = [] # bottles of potions

    while r_ml_held > 500: # while I have red ml to bottle
        r_potions_gained += 1
        r_ml_held -= 100
    
    if r_potions_gained > 0:
        bottle_lst.append({"potion_type": [100, 0, 0, 0], "quantity": r_potions_gained})
    
    while g_ml_held > 500: # while I have green ml to bottle
        g_potions_gained += 1
        g_ml_held -= 100

    if g_potions_gained > 0:
        bottle_lst.append({"potion_type": [0, 100, 0, 0], "quantity": g_potions_gained})
    
    while b_ml_held > 500: # while I have blue ml to bottle
        b_potions_gained += 1
        b_ml_held -= 100
    
    if b_potions_gained > 0:
        bottle_lst.append({"potion_type": [0, 0, 100, 0], "quantity": b_potions_gained})

    while d_ml_held > 500: # while I have dark ml to bottle
        d_potions_gained += 1
        d_ml_held -= 100
    
    if d_potions_gained > 0:
        bottle_lst.append({"potion_type": [0, 0, 0, 100], "quantity": d_potions_gained})

    # custom bottling (just purple for now)
    while r_ml_held >= 50 and b_ml_held >= 50: # while I have ml to bottle purple potions
        p_potions_gained += 1
        r_ml_held -= 50
        b_ml_held -= 50
    
    if p_potions_gained > 0:
        bottle_lst.append({"potion_type": [50, 0, 50, 0], "quantity": p_potions_gained})
    
    return bottle_lst
