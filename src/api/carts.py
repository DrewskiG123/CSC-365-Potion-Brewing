from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }

# GOES SOMEWHERE BUT FIGURING OUT WHERE
# price per ml by color
    # r_ppm = .5  # so a red potion is .5 * 100 = 50 gold
    # g_ppm = .5  # same for green
    # b_ppm = .6  # blue is .6 * 100 = 60 gold
    # d_ppm = .65 # dark is .65 * 100 = 65 gold
    # other potions will be multiplied by these constants to get their sale price
    #                     [r , g, b , d]   (r_ml * r_ppm) + (b_ml * b_ppm)
    # ex: Purple potion = [50, 0, 50, 0], so (50 * .5)    +   (50 * .6) = 25 + 30 = 55, 
    # so purple will cost 55 gold

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
                "quantity": quant
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
        ctlg_stuff = connection.execute(sqlalchemy.text("SELECT id FROM catalog WHERE sku = :item_sku"), [{"item_sku": item_sku}])
        ctlg_id = ctlg_stuff.first()._data[0]
        print("catalog id received:", ctlg_id)
        connection.execute(sqlalchemy.text("""
            IF EXISTS (SELECT quantity FROM cart_items WHERE cart_id = :cart_id AND catalog_id = :ctlg_id) THEN
                UPDATE cart_items SET quantity = quantity + :quantity
                WHERE cart_id = :cart_id AND catalog_id = :ctlg_id
            END IF;
            ELSE
              INSERT INTO cart_items (cart_id, quantity, catalog_id)
              SELECT :cart_id, :quantity, catalog.id
              FROM catalog WHERE catalog.sku = :item_sku
        """), [{"cart_id": cart_id, "ctlg_id": ctlg_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
        # connection.execute(sqlalchemy.text("""
        #     INSERT INTO cart_items (cart_id, quantity, catalog_id)
        #     SELECT :cart_id, :quantity, catalog.id
        #     FROM catalog WHERE catalog.sku = :item_sku
        # """), [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
    
    return {"success": True}
        
class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ Complete customer transaction """
    if cart_checkout != None and cart_checkout.payment != None: # offered payment
        pots_bought = 0
        cost = 0
        # There's gotta be a more efficent way to do this
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("""
                SELECT id, price, catalog.quantity FROM catalog
                JOIN cart_items ON cart_items.catalog_id = catalog.id
                """), [{"cart_id": cart_id}])

            for id, price, quantity in result:
                print("id:", id, ", price:", price, ", # bought:", quantity)
                pots_bought += quantity
                cost += (quantity * price)

                connection.execute(sqlalchemy.text("""
                    INSERT INTO catalog_tracker (sku, potion_type, change)
                    SELECT catalog.sku, catalog.potion_type, :quantity
                    FROM catalog WHERE catalog.id = :id
                    """), [{"id": id, "quantity": (0-quantity)}])

                sku_cursor = connection.execute(sqlalchemy.text("""
                    SELECT sku FROM catalog
                    WHERE catalog.id = :id
                """), [{"id":id}])
                sku_received = sku_cursor.first()._data[0]
                
                sum_cursor = connection.execute(sqlalchemy.text("""
                    SELECT SUM(change) 
                    FROM catalog_tracker
                    WHERE catalog_tracker.sku = :sku
                """), [{"sku": sku_received}])
                sum = sum_cursor.first()._data[0]
                
                connection.execute(sqlalchemy.text("""
                    UPDATE catalog
                    SET quantity = :sum
                    WHERE id = :id
                """), [{"sum": sum, "id": id}])
            
            connection.execute(sqlalchemy.text("""
                INSERT INTO global_inventory (gold)
                VALUES(:cost)
                """), [{"cost": cost}])
        
    return {"total_potions_bought": pots_bought, "total_gold_paid": cost}
