from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

import copy

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

def get_barrel_color(barrel_sku: str):
    """ Checks sku to get barrel color. """
    if barrel_sku.__contains__("RED"):
        return 1
    elif barrel_sku.__contains__("GREEN"):
        return 2
    elif barrel_sku.__contains__("BLUE"):
        return 3
    else: # dark barrels in the future?
        return 4
    
def get_barrel_size(barrel_sku: str):
    """ Checks sku to get barrel size. """
    if barrel_sku.__contains__("MEDIUM"):
        return 1
    elif barrel_sku.__contains__("SMALL"):
        return 2
    elif barrel_sku.__contains__("MINI"):
        return 3
    else: # other sizes in the future?
        return 4

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ Handles barrel reception (updating ml and gold) """
    print(barrels_delivered)

    r_ml_held = -1
    r_ml_added = 0
    g_ml_held = -1
    g_ml_added = 0
    b_ml_held = -1
    b_ml_added = 0

    med_ml = 2500
    small_ml = 500
    mini_ml = 200

    for barrel in barrels_delivered:
        color = get_barrel_color(barrel.sku)
        size = get_barrel_size(barrel.sku)
        combo = (color, size)
        match combo:
            case (1,1): # RED MED
                r_ml_added = (med_ml * barrel.quantity)
            case (1,2): # RED SMALL
                r_ml_added = (small_ml * barrel.quantity)
            case (1,3): # RED MINI
                r_ml_added = (mini_ml * barrel.quantity)
            case (2,1): # GREEN MED
                g_ml_added = (med_ml * barrel.quantity)
            case (2,2): # GREEN SMALL
                g_ml_added = (small_ml * barrel.quantity)
            case (2,3): # GREEN MINI
                g_ml_added = (mini_ml * barrel.quantity)
            case (3,1): # BLUE MED
                b_ml_added = (med_ml * barrel.quantity)
            case (3,2): # BLUE SMALL
                b_ml_added = (small_ml * barrel.quantity)
            case (3,3): # BLUE MINI
                b_ml_added = (mini_ml * barrel.quantity)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = result.first()
        
        r_ml_held = fr.num_red_ml
        g_ml_held = fr.num_green_ml
        b_ml_held = fr.num_blue_ml
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(r_ml_held + r_ml_added) + " WHERE id = 0"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = " + str(g_ml_held + g_ml_added) + " WHERE id = 0"))
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = " + str(b_ml_held + b_ml_added) + " WHERE id = 0"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ Returns what barrels to purchase to keep stocks up.
     Larger barrels are more cost efficient. 
     Barrels go: rMed, rSmall, gMed, gSmall, bMed, bSmall, rMini, gMini, bMini """

    print(wholesale_catalog)

    gold_held = -1

    r_potions_held = -1
    r_ml_held = -1

    g_potions_held = -1
    g_ml_held = -1

    b_potions_held = -1
    b_ml_held = -1
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = result.first()
        gold_held = fr.gold
        r_potions_held = fr.num_red_potions
        r_ml_held = fr.num_red_ml
        g_potions_held = fr.num_green_potions
        g_ml_held = fr.num_green_ml
        b_potions_held = fr.num_blue_potions
        b_ml_held = fr.num_blue_ml

    purchase_plan = []

    need_r = False
    need_g = False
    need_b = False

    needed = 0

    if r_potions_held < 10 and r_ml_held < 1000:
        need_r = True
        needed += 1
    if g_potions_held < 10 and g_ml_held < 1000:
        need_g = True
        needed += 1
    if b_potions_held < 10 and b_ml_held < 1000:
        need_b = True
        needed += 1

    if needed > 0: # if some barrels are needed
        gold_per_color = gold_held//needed
        for barrel in wholesale_catalog:
            if barrel.potion_type[0] == 1 and barrel.price < gold_per_color and barrel.price < gold_held and need_r == True: # if its an affordable red barrel
                purchase_plan.append(
                    {
                        "sku":barrel.sku,
                        "ml_per_barrel": barrel.ml_per_barrel,
                        "potion_type": barrel.potion_type,
                        "price": barrel.price,
                        "quantity": 1
                    })
                gold_held -= barrel.price
                need_r = False
            elif barrel.potion_type[1] == 1 and barrel.price < gold_per_color and barrel.price < gold_held and need_g == True: # if its an affordable green barrel
                purchase_plan.append(
                    {
                        "sku":barrel.sku,
                        "ml_per_barrel": barrel.ml_per_barrel,
                        "potion_type": barrel.potion_type,
                        "price": barrel.price,
                        "quantity": 1
                    })
                gold_held -= barrel.price
                need_g = False
            elif barrel.potion_type[2] == 1 and barrel.price < gold_per_color and barrel.price < gold_held and need_b == True: # if its an affordable blue barrel
                purchase_plan.append({
                        "sku":barrel.sku,
                        "ml_per_barrel": barrel.ml_per_barrel,
                        "potion_type": barrel.potion_type,
                        "price": barrel.price,
                        "quantity": 1
                    })
                gold_held -= barrel.price
                need_b = False

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(gold_held) + " WHERE id = 0"))

    return purchase_plan
