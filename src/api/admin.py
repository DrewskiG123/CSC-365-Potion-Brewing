from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("TRUNCATE TABLE cart_items, carts, catalog, catalog_tracker, global_inventory;"))
        connection.execute(sqlalchemy.text("""
            INSERT INTO global_inventory (num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold)
            VALUES (0, 0, 0, 0, 100);"""))
        connection.execute(sqlalchemy.text("""
            INSERT INTO catalog (sku, name, price, potion_type, quantity)
            VALUES
                ('RED_POTION', 'Health', 50, :r_type, 0),
                ('GREEN_POTION', 'Stamina', 50, :g_type, 0),
                ('BLUE_POTION', 'Mana', 60, :b_type, 0),
                ('DARK_POTION', 'Dark', 65, :d_type, 0);"""), 
        [{"r_type": [100,0,0,0], "g_type": [0,100,0,0], "b_type": [0,0,100,0], "d_type": [0,0,0,100]}])
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ Returns shop info """
    return {
        "shop_name": "DREW'S BREWS",
        "shop_owner": "Andrew Ji",
    }

