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


class NewCart(BaseModel):
    customer: str
    cart_id: int
    item_type: str
    amount: int

cart_lst = []
id_num = 0

@router.post("/")
def create_cart(new_cart: NewCart):
    """ Adds a cart to the cart list """
    global cart_lst
    global id_num
    
    new_cart.cart_id = id_num
    cart_lst.append(new_cart)
    id_num += 1 # increments id so they don't overlap

    return {"cart_id": id_num}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ Grabs a cart from the list based on index (cart_id) """
    return cart_lst[cart_id]


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ Updates the cart with the desired commoditites """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory WHERE id = 0"))
        # fr is the first row of global_inventory
        fr = result.first()
        red_pots_held = fr.num_red_potions

    if cart_id < len(cart_lst): # if it's a valid cart
        if item_sku == "RED_POTION_0" and cart_item.quantity < red_pots_held: # only handling red potions for now
            cur_cart = cart_lst[cart_id]
            cur_cart.item_type = "RED_POTION_0"
            cur_cart.amount = cart_item.quantity
            return "OK"
        else:
            return "NOT ENOUGH STOCK"
    else:
        return "INVALID CART"
        

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ Complete customer transaction """
    cur_cart = cart_lst[cart_id]
    return {"total_potions_bought":  cur_cart.amount, "total_gold_paid": int(cart_checkout.payment)}
