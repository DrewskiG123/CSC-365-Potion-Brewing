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

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ Handles barrel reception (updating ml and gold) """
    
    print(barrels_delivered)
    
    gold_held = -1
    cost = 0

    r_ml_held = -1
    r_ml_added = 0
    g_ml_held = -1
    g_ml_added = 0
    b_ml_held = -1
    b_ml_added = 0

    for barrel in barrels_delivered:
        if barrel.potion_type[0] == 1 and barrel.quantity > 0: # red barrels
            cost += (barrel.price * barrel.quantity)
            r_ml_added += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type[1] == 1 and barrel.quantity > 0: # green barrels
            cost += (barrel.price * barrel.quantity)
            g_ml_added += (barrel.ml_per_barrel * barrel.quantity)
        elif barrel.potion_type[2] == 1 and barrel.quantity > 0: # blue barrels
            cost += (barrel.price * barrel.quantity)
            b_ml_added += (barrel.ml_per_barrel * barrel.quantity)

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = result.first()
        
        gold_held = fr.gold
        r_ml_held = fr.num_red_ml
        g_ml_held = fr.num_green_ml
        b_ml_held = fr.num_blue_ml
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(gold_held - cost) + " WHERE id = 0"))
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

    gold_per_color = gold_held//needed
    for barrel in wholesale_catalog:
        if barrel.potion_type[0] == 1 and barrel.price < gold_per_color and barrel.price < gold_held and need_r == True: # if its an affordable red barrel
            b = copy.deepcopy(barrel)
            b.quantity = 1
            purchase_plan.append(b)
            gold_held -= b.price
            need_r = False
        elif barrel.potion_type[1] == 1 and barrel.price < gold_per_color and barrel.price < gold_held and need_g == True: # if its an affordable green barrel
            b = copy.deepcopy(barrel)
            b.quantity = 1
            purchase_plan.append(b)
            gold_held -= b.price
            need_g = False
        elif barrel.potion_type[2] == 1 and barrel.price < gold_per_color and barrel.price < gold_held and need_b == True: # if its an affordable blue barrel
            b = copy.deepcopy(barrel)
            b.quantity = 1
            purchase_plan.append(b)
            gold_held -= b.price
            need_b = False

    return purchase_plan
