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
        # result.first() is the first row of global_inventory
        red_potions_held = result.first().num_red_potions

    if red_potions_held > 0:
        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": red_potions_held,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
    else:
        return []
