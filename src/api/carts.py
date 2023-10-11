from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

from src.api import catalog

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class CartItem(BaseModel):
    quantity: int

class NewCart(BaseModel):
    customer: str

# cart_id will correspond to the lists
cart_lst = []  # list of names
item_lst = [[],[],[],[]]  # list of skus (list of str[])
quant_lst = [[],[],[],[]] # list of of quantities (list of int[])
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
    myPrices = []
    for sku in item_lst[cart_id]:
        myPrices.append(catalog.prices[sku])

    return{
        "name": cart_lst[cart_id], 
        "items": item_lst[cart_id], 
        "quantities": quant_lst[cart_id],
        "prices": myPrices
    }

def s_i_q_helper(cart_id: int, sku: str, quant: int, q_lst_index: int, limit: int):
    """ Helps reduce repeat code in set_item_quantity() """
    cur_items = item_lst[cart_id]
    cur_quant_lst = quant_lst[cart_id]

    if sku in cur_items and (cur_quant_lst[q_lst_index] + quant) < limit: # if it already has the potions added and is adding more
        cur_quant_lst[q_lst_index] += quant # index that matches the index of the sku
        return "OK"
    elif q_lst_index == -1: # adding a new item to the cart, quant is ok if it's here
        cur_items.append(sku)
        cur_quant_lst.append(quant)
        return "OK"
    else:
        return "CANNOT INCREASE BY DESIRED AMOUNT"

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
        quant = cart_item.quantity
        q_lst_index = -1
        if item_sku in item_lst[cart_id]:
            q_lst_index = item_lst[cart_id].index(item_sku)

        match item_sku:
            case "RED_POTION_0":
                if quant < r_pots_held:
                    return s_i_q_helper(cart_id, item_sku, quant, q_lst_index, r_pots_held)
            case "GREEN_POTION_0":
                if quant < g_pots_held:
                    return s_i_q_helper(cart_id, item_sku, quant, q_lst_index, g_pots_held)
            case "BLUE_POTION_0":
                if quant < b_pots_held:
                    return s_i_q_helper(cart_id, item_sku, quant, q_lst_index, b_pots_held)
            case _:
                return "ERROR PROCESSING CART"
    else:
        return "INVALID CART ID", "ID", cart_id, "len", len(cart_lst)
        
class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ Complete customer transaction """
    cur_items = item_lst[cart_id]
    cur_q_lst = quant_lst[cart_id]
    cost_of_cart = 0

    red = "RED_POTION_0"
    green = "GREEN_POTION_0"
    blue = "BLUE_POTION_0"

    # payment_offered = int(cart_checkout.payment)

    i = 0
    for sku in cur_items: # for every item type purchased
        cost_of_cart += (catalog.prices[sku] * cur_q_lst[i]) # increase cost by price*amount
        i += 1 # advance index of quantity list to match item

    # if cost_of_cart > payment_offered:
    #     return "NOT ENOUGH PAYMENT", "COST", cost_of_cart, "OFFERED", payment_offered
    # else: # update table and return
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory WHERE id = 0"))
        # fr is the first row of global_inventory
        fr = result.first()
        gold_held = fr.gold
        r_pots_held = fr.num_red_potions
        g_pots_held = fr.num_green_potions
        b_pots_held = fr.num_blue_potions

        if red in cur_items:
            r_amnt = cur_q_lst[cur_items.index(red)]
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = " + str(r_pots_held - r_amnt) + " WHERE id = 0") )
        if green in cur_items:
            g_amnt = cur_q_lst[cur_items.index(green)]
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = " + str(g_pots_held - g_amnt) + " WHERE id = 0") )
        if blue in cur_items:
            b_amnt = cur_q_lst[cur_items.index(blue)]
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = " + str(b_pots_held - b_amnt) + " WHERE id = 0") )
        # gold
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(gold_held + cost_of_cart) + " WHERE id = 0") )   
        return {"total_potions_bought": sum(cur_q_lst), "total_gold_paid": cart_checkout.payment}
