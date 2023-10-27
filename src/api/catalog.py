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
        result = connection.execute(sqlalchemy.text("SELECT sku, name, quantity, potion_type, price FROM catalog ORDER BY id"))
        for sku, name, quantity, potion_type, price in result:
            # cur_quant = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM catalog_tracker WHERE sku = :sku"), [{"sku": sku}])
            print(f"{{\n\tname: {name},\n\tsku: {sku},\n\tpotion_type: {potion_type},\n\tquantity: {quantity},\n\tprice: {price}\n}}")
            if quantity != None and quantity > 0:
                catalog.append({
                    "sku": sku, 
                    "name": name, 
                    "quantity": quantity,#cur_quant.first()._data[0],
                    "potion_type": potion_type, 
                    "price": price})

    return catalog
