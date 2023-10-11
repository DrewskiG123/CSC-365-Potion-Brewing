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
                "UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(r_ml_added) + ",\n"+
                "   num_green_ml = num_green_ml + " + str(g_ml_added) + ",\n"+
                "   num_blue_ml = num_blue_ml + " + str(b_ml_added) + ",\n"+
                "   gold = gold - " + str(cost) + " WHERE id = 0"))

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

    return purchase_plan
