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
    print("Get Catalog")
    catalog = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT name, sku, potion_type, inventory, price FROM potions"))
        for name, sku, potion_type, inventory, price in result:
            print(f"{{\n\tname: {name},\n\tsku: {sku},\n\ttype: {potion_type},\n\tinventory: {inventory},\n\tprice: {price}\n}}")
            catalog.append({
                "name": name, 
                "sku": sku, 
                "type": potion_type, 
                "inventory": inventory, 
                "price": price})

    return catalog
