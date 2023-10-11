from fastapi import APIRouter

import sqlalchemy
from src import database as db

router = APIRouter()

prices = {"RED_POTION_0": 10, "GREEN_POTION_0": 10, "BLUE_POTION_0": 10} # dictionary of prices thats shared with carts.py

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        # fr is the first row of global_inventory
        fr = result.first()
        r_potions_held = fr.num_red_potions
        g_potions_held = fr.num_green_potions
        b_potions_held = fr.num_blue_potions

    ret_lst = []

    if r_potions_held > 0:
        ret_lst.append(
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": r_potions_held,
                "price": prices["RED_POTION_0"],
                "potion_type": [100, 0, 0, 0],
            }
        )
    if g_potions_held > 0:
        ret_lst.append(
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": g_potions_held,
                "price": prices["GREEN_POTION_0"],
                "potion_type": [0, 100, 0, 0],
            }
        )
    if b_potions_held > 0:
        ret_lst.append(
            {
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": b_potions_held,
                "price": prices["BLUE_POTION_0"],
                "potion_type": [0, 0, 100, 0],
            }
        )

    return ret_lst
