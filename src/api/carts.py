from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class CartItem(BaseModel):
    quantity: int

class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
    """ Adds a cart to the cart table """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO carts (customer) VALUES (:customer)"), [{"customer": new_cart.customer}])
        result = connection.execute(sqlalchemy.text("SELECT id FROM carts WHERE customer = (:customer)"), [{"customer": new_cart.customer}])
    return {"cart_id": result.first().id}

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ Grabs a cart from the list based on index (cart_id) """
    cart_items_lst = []
    with db.engine.begin() as connection:
        carts_result = connection.execute(sqlalchemy.text("""
            SELECT * FROM carts WHERE id = (:id)
            """), [{"id": cart_id}])
        fr = carts_result.first()

        items_result = connection.execute(sqlalchemy.text("""
            SELECT catalog_id, quantity FROM cart_items WHERE cart_id = (:id)
            """), [{"id": cart_id}])
        
        for cat_id, quant in items_result:
            cart_items_lst.append({
                "catalog_id": cat_id,
                "quant": quant
            })

    return {
        "cart_id": fr.id,
        "customer": fr.customer,
        "time_created": fr.created_at,
        "cart": cart_items_lst}

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ Updates the cart with the desired commoditites """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
            INSERT INTO cart_items (cart_id, quantity, catalog_id)
            SELECT :cart_id, :quantity, catalog.id
            FROM catalog WHERE catalog.sku = :item_sku"""), [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
    
    return {"success": True}
        
class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ Complete customer transaction """
    if cart_checkout != None and cart_checkout.payment != None: # offered payment
        pots_bought = 0
        cost = 0
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("""
                SELECT id, price, quantity FROM catalog
                JOIN cart_items ON cart_items.catalog_id = catalog.id
                """), [{"cart_id": cart_id}])

            for id, price, quantity in result:
                print("id:", id, ", price:", price, ", # bought:", quantity)
                pots_bought += quantity
                cost += (quantity * price)
            
            connection.execute(sqlalchemy.text("""
                UPDATE catalog
                SET inventory = catalog.inventory - cart_items.quantity
                FROM cart_items
                WHERE catalog.id = cart_items.catalog_id and cart_items.cart_id = :cart_id
                """), [{"cart_id": cart_id}])
            
            connection.execute(sqlalchemy.text("""
                UPDATE global_inventory
                SET gold = global_inventory.gold - :cost
                """), [{"cost": cost}])
        
    return {"total_potions_bought": pots_bought, "total_gold_paid": cost}
