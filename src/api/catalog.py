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
        result = connection.execute(sqlalchemy.text("SELECT name, sku, potion_type, quantity, price FROM catalog"))
        for name, sku, potion_type, quantity, price in result:
            print(f"{{\n\tname: {name},\n\tsku: {sku},\n\ttype: {potion_type},\n\tquantity: {quantity},\n\tprice: {price}\n}}")
            catalog.append({
                "name": name, 
                "sku": sku, 
                "type": potion_type, 
                "quantity": quantity, 
                "price": price})

    return catalog
