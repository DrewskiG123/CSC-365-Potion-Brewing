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
            connection.execute(sqlalchemy.text("""
                INSERT INTO catalog_tracker (sku, change)
                SELECT catalog.sku, :change
                FROM catalog WHERE catalog.potion_type = :potion_type
            """), [{"change": pot.quantity, "potion_type": pot.potion_type}])
        
        profit += r_ml_used * r_ppm # cost of red component in these pots
        profit += g_ml_used * g_ppm # cost of green component in these pots
        profit += b_ml_used * b_ppm # cost of blue component in these pots
        profit += d_ml_used * d_ppm # cost of dark component in these pots
        
        connection.execute(sqlalchemy.text("""
            INSERT INTO global_inventory
            VALUES (:r_ml_added, :g_ml_added, :b_ml_added, :d_ml_added, :profit)
        """),
        [{"r_ml_used": r_ml_used, "g_ml_used": g_ml_used, "b_ml_used": b_ml_used, "d_ml_used": d_ml_used, "profit": profit}])

    return "OK"

class State(BaseModel):
    '''current shop resource state'''
    red_ml: int
    green_ml: int
    blue_ml: int
    dark_ml: int
    my_pots: list[PotionInventory]

def mix_potions(state: State, color_weight: list[int]):
    '''
    The logic that determines the bottling plan based on my current shop state (very simple currently).
    Returns the bottle plan.
    '''
    plan = []
    for pot in state.my_pots:
        print(pot)
        if pot.quantity < 10: # if I have <10 and enough mils to make one
            if (pot.potion_type[0] < state.red_ml and 
                pot.potion_type[1] < state.green_ml and 
                pot.potion_type[2] < state.blue_ml and 
                pot.potion_type[3] < state.dark_ml):
                plan.append(
                    {
                        "potion_type": pot.potion_type,
                        "quantity": 1
                    }
                )
                state.red_ml -= pot.potion_type[0]
                state.blue_ml -= pot.potion_type[1]
                state.green_ml -= pot.potion_type[2]
                state.dark_ml -= pot.potion_type[3]


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
        r_ml_held = connection.execute(sqlalchemy.text("SELECT SUM(num_red_ml) FROM global_inventory"))
        g_ml_held = connection.execute(sqlalchemy.text("SELECT SUM(num_green_ml) FROM global_inventory"))
        b_ml_held = connection.execute(sqlalchemy.text("SELECT SUM(num_blue_ml) FROM global_inventory"))
        d_ml_held = connection.execute(sqlalchemy.text("SELECT SUM(num_dark_ml) FROM global_inventory"))
        r = r_ml_held.first()._data[0]
        g = g_ml_held.first()._data[0]
        b = b_ml_held.first()._data[0]
        d = d_ml_held.first()._data[0]

        color_weight = [0,0,0,0]
        
        pots_held = []
        ctlg = connection.execute(sqlalchemy.text("SELECT sku, potion_type FROM catalog"))
        for sku, potion_type in ctlg:
            cur_quant = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM catalog_tracker WHERE sku = :sku"), [{"sku": sku}])
            pots_held.append({
                "potion_type": potion_type,
                "quantity": cur_quant.first()._data[0]
            })
            for i in range(4):
                color_weight[i] += potion_type[i]

    state = State(red_ml=r, 
                  green_ml=g,
                  blue_ml=b,
                  dark_ml=d,
                  my_pots=pots_held)
    
    return mix_potions(state, color_weight)
