from fastapi import APIRouter

import sqlalchemy
from src import database as db

router = APIRouter()


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
        red_potions_held = fr.num_red_potions

    ret_lst = []

    if red_potions_held > 0:
        ret_lst.append(
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": red_potions_held,
                "price": 10,
                "potion_type": [100, 0, 0, 0],
            }
        )

    return ret_lst
