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
    """ Handling inventory after bottling """
    print(potions_delivered)

    # price per ml by color
    r_ppm = .5  # so a red potion is .5 * 100 = 50 gold
    g_ppm = .5  # same for green
    b_ppm = .6  # blue is .6 * 100 = 60 gold
    d_ppm = .65 # dark is .65 * 100 = 65 gold
    # other potions will be multiplied by these constants to get their sale price
    #                     [r , g, b , d]   (r_ml * r_ppm) + (b_ml * b_ppm)
    # ex: Purple potion = [50, 0, 50, 0], so (50 * .5)    +   (50 * .6) = 25 + 30 = 55, 
    # so purple will cost 55 gold

    r_ml_used = 0
    g_ml_used = 0
    b_ml_used = 0
    d_ml_used = 0
    profit = 0

    with db.engine.begin() as connection: # this should work regardless of how many pots or what type
        for pot in potions_delivered:
            r_ml_used += pot.potion_type[0] * pot.quantity  # red ml used in these pots
            g_ml_used += pot.potion_type[1] * pot.quantity  # green ml used in these pots
            b_ml_used += pot.potion_type[2] * pot.quantity  # blue ml used in these pots
            d_ml_used += pot.potion_type[3] * pot.quantity  # dark ml used in these pots
            connection.execute(sqlalchemy.text(
                "UPDATE catalog SET quantity = quantity + :add_quant WHERE potion_type = :type"), 
                [{"add_quant": pot.quantity, "type": pot.potion_type}])
        
        profit += r_ml_used * r_ppm # cost of red component in these pots
        profit += g_ml_used * g_ppm # cost of green component in these pots
        profit += b_ml_used * b_ppm # cost of blue component in these pots
        profit += d_ml_used * d_ppm # cost of dark component in these pots
        
        connection.execute(sqlalchemy.text("""
            UPDATE global_inventory 
            SET num_red_ml = num_red_ml - :r_ml_used,
                num_green_ml = num_green_ml - :g_ml_used,
                num_blue_ml = num_blue_ml - :b_ml_used,
                num_dark_ml = num_dark_ml - :d_ml_used,
                gold = gold + :profit
            WHERE id = 0 """), 
        [{"r_ml_used": r_ml_used, "g_ml_used": g_ml_used, "b_ml_used": b_ml_used, "d_ml_used": d_ml_used, "profit": profit}])

    return "OK"

class State(BaseModel):
    '''current shop resource state'''
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int
    my_pots: list[PotionInventory]

def mix_potions(state: State):
    '''
    The logic that determines the bottling plan based on my current shop state.
    Returns the bottle plan.
    '''
    plan = []
    for pot in state.my_pots:
        print(pot)
    return plan

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

    with db.engine.begin() as connection:
        glbl_inv = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = glbl_inv.first()
        r_ml_held = fr.num_red_ml
        g_ml_held = fr.num_green_ml
        b_ml_held = fr.num_blue_ml
        d_ml_held = fr.num_dark_ml
        
        pots_held = []
        ctlg = connection.execute(sqlalchemy.text("SELECT potion_type, quantity FROM catalog"))
        for type, quant in ctlg:
            pots_held.append({
                "potion_type": type,
                "quantity": quant
            })

    state = State(red_ml=r_ml_held, 
                  green_ml=g_ml_held,
                  blue_ml=b_ml_held,
                  dark_ml=d_ml_held,
                  my_pots=pots_held)
    
    return mix_potions(state)
