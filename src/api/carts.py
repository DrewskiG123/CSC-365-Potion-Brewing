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

cart_lst = []
id_num = 0

@router.post("/")
def create_cart(new_cart: NewCart):
    """ Adds a cart to the cart list """
    global cart_lst
    global id_num
    
    cart_lst.append(new_cart)
    id_num += 1 # increments id so they don't overlap

    return {"cart_id": id_num-1}

@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ Grabs a cart from the list based on index (cart_id) """
    return cart_lst[cart_id]

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ Updates the cart with the desired commoditites """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id = 0"))
        # fr is the first row of global_inventory
        fr = result.first()
        r_pots_held = fr.num_red_potions
        g_pots_held = fr.num_green_potions
        b_pots_held = fr.num_blue_potions

    if cart_id < len(cart_lst): # if it's a valid cart
        cur_cart = cart_lst[cart_id]

        if item_sku == "RED_POTION_0" and cart_item.quantity <= r_pots_held:
            return "OK"
        elif item_sku == "GREEN_POTION_0" and cart_item.quantity <= g_pots_held:
            return "OK"
        elif item_sku == "BLUE_POTION_0" and cart_item.quantity <= b_pots_held:
            return "OK"
        else:
            return "ERROR PROCESSING CART"
    else:
        return "INVALID CART ID"
        
class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ Complete customer transaction """
    cur_cart = cart_lst[cart_id]
    
    return {"total_potions_bought": cur_cart.item.quantity, "total_gold_paid": int(cart_checkout.payment)}
