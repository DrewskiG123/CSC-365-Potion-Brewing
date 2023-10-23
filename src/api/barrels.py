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

    r_ml_added = 0
    g_ml_added = 0
    b_ml_added = 0
    d_ml_added = 0

    cost = 0

    for barrel in barrels_delivered:
        type = barrel.potion_type
        match type:
            case [1,0,0,0]: # RED BARREL
                r_ml_added += (barrel.ml_per_barrel * barrel.quantity)
            case [0,1,0,0]: # GREEN BARREL
                g_ml_added += (barrel.ml_per_barrel * barrel.quantity)
            case [0,0,1,0]: # BLUE BARREL
                b_ml_added += (barrel.ml_per_barrel * barrel.quantity)
            case [0,0,0,1]: # DARK BARREL
                d_ml_added += (barrel.ml_per_barrel * barrel.quantity)
        cost += (barrel.price * barrel.quantity)

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
            """ UPDATE global_inventory 
                SET num_red_ml = num_red_ml + :r_ml_added,
                    num_green_ml = num_green_ml + :g_ml_added,
                    num_blue_ml = num_blue_ml + :b_ml_added,
                    num_dark_ml = num_dark_ml + :d_ml_added,
                    gold = gold - :cost 
                WHERE id = 0
            """), [{"r_ml_added": r_ml_added, "g_ml_added": g_ml_added, "b_ml_added": b_ml_added, "d_ml_added": d_ml_added, "cost": cost}]) 

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Returns what barrels to purchase to keep stocks up.
    Larger barrels are more cost efficient. 
    Barrels go: rMed, rSmall, gMed, gSmall, bMed, bSmall, rMini, gMini, bMini
    """
    print(wholesale_catalog)

    gold_held = -1
    r_ml_held = -1
    g_ml_held = -1
    b_ml_held = -1
    d_ml_held = -1
    
    with db.engine.begin() as connection:
        glbl_inv = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = glbl_inv.first()
        r_ml_held = fr.num_red_ml
        g_ml_held = fr.num_green_ml
        b_ml_held = fr.num_blue_ml
        d_ml_held = fr.num_dark_ml
        gold_held = fr.gold

    purchase_plan = []

    need_r = False
    need_g = False
    need_b = False
    need_d = False

    needed = 0

    # very simple logic to buy barrels
    if r_ml_held < 1000:
        need_r = True
        needed += 1
    if g_ml_held < 1000:
        need_g = True
        needed += 1
    if b_ml_held < 1000:
        need_b = True
        needed += 1
    if d_ml_held < 1000:
        need_d = True
        needed += 1

    if needed > 0: # if some barrels are needed
        gold_per_color = gold_held//needed
        for barrel in wholesale_catalog:
            if barrel.price < gold_per_color and barrel.price < gold_held: 
                if barrel.potion_type[0] == 1 and need_r == True: # if its an affordable red barrel
                    need_r = False
                elif barrel.potion_type[1] == 1 and need_g == True: # if its an affordable green barrel
                    need_g = False
                elif barrel.potion_type[2] == 1 and need_b == True: # if its an affordable blue barrel
                    need_b = False
                elif barrel.potion_type[3] == 1 and need_d == True: # if its an affordable dark barrel
                    need_d = False
                else:
                    continue
                
                purchase_plan.append(
                    {
                        "sku":barrel.sku,
                        "ml_per_barrel": barrel.ml_per_barrel,
                        "potion_type": barrel.potion_type,
                        "price": barrel.price,
                        "quantity": 1
                    })
                gold_held -= barrel.price

    return purchase_plan
