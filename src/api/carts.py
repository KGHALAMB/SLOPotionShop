import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

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
    customer_name: str = "", #search for this customer
    potion_sku: str = "", #search for this sku
    search_page: str = "1", # idk dude like whaaaat
    sort_col: search_sort_options = search_sort_options.timestamp, #automatically sorts by timestamp
    sort_order: search_sort_order = search_sort_order.desc, #automatically sorts by desc
):
    if search_page != "1":
        previous = str(int(search_page) - 1)
    else: 
        previous = ""

    metadata_obj = sqlalchemy.MetaData()
    cart_items = sqlalchemy.Table("cart_items", metadata_obj, autoload_with=db.engine)
    carts = sqlalchemy.Table("carts", metadata_obj, autoload_with=db.engine)
    catalog_items = sqlalchemy.Table("catalog_items", metadata_obj, autoload_with=db.engine)
    stmt = (
        sqlalchemy.select(
            cart_items.c.id,
            catalog_items.c.sku,
            catalog_items.c.price,
            carts.c.name,
            cart_items.c.created_at,
            cart_items.c.quantity
        )
        .join(carts, cart_items.c.cart == carts.c.id)
        .join(catalog_items, catalog_items.c.id == cart_items.c.item_id)
        .offset((int(search_page) - 1) * 5)
        .limit(6)
        .where(carts.c.checked_out == True)
        )
    if customer_name != "":
        stmt = stmt.where(carts.c.name == customer_name)
    if potion_sku != "":
        stmt = stmt.where(catalog_items.c.sku == potion_sku)

    if sort_col is search_sort_options.customer_name:
        if sort_order == search_sort_order.asc:
            stmt = stmt.order_by(sqlalchemy.asc(carts.c.name))
        else:
            stmt = stmt.order_by(sqlalchemy.desc(carts.c.name))
    elif sort_col is search_sort_options.item_sku:
        if sort_order == search_sort_order.asc:
            stmt = stmt.order_by(sqlalchemy.asc(catalog_items.c.sku))
        else:
            stmt = stmt.order_by(sqlalchemy.desc(catalog_items.c.sku))
    elif sort_col is search_sort_options.line_item_total:
        if sort_order == search_sort_order.asc:
            stmt = stmt.order_by(sqlalchemy.asc(catalog_items.c.price * cart_items.c.quantity))
        else:
            stmt = stmt.order_by(sqlalchemy.desc(catalog_items.c.price * cart_items.c.quantity))
    elif sort_col is search_sort_options.timestamp:
        if sort_order == search_sort_order.asc:
            stmt = stmt.order_by(sqlalchemy.asc(cart_items.c.created_at))
        else:
            stmt = stmt.order_by(sqlalchemy.desc(cart_items.c.created_at))    
    with db.engine.begin() as connection:
        res = connection.execute(stmt)
        res = res.all()
        line_item = []
        if len(res) > 5:
            next = str(int(search_page) + 1)
        else: 
            next = ""
        res = res[:5]
        for row in res:
            print(row)
            line_item.append (
                {
                    "line_item_id": row[0],
                    "item_sku": row[1],
                    "customer_name": row[3],
                    "line_item_total": row[2] * row[5],
                    "timestamp": row[4]
                }
            )
        
        """offset = 0 * search_page
        if sort_col is search_sort_options.customer_name:
            order_by = db.movies.c.title
        elif sort_col is search_sort_options.item_sku:
            order_by = db.movies.c.year
        elif sort_col is search_sort_options.rating:
            order_by = sqlalchemy.desc(db.movies.c.imdb_rating)
        else:
            assert False"""

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
        "previous": previous,
        "next": next,
        "results": line_item
    }


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (name) \
                                                    VALUES (:name) \
                                                    RETURNING id"),
                                                    {"name": new_cart.customer}).first()[0]
    return {"cart_id": result}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart, quantity, item_id) \
                                                    SELECT :cart_id, :quantity, catalog_items.id \
                                                    FROM catalog_items \
                                                    WHERE catalog_items.sku = :item_sku"), 
                                                    {"cart_id" : cart_id,
                                                     "quantity" : cart_item.quantity,
                                                     "item_sku" : item_sku})
        
        transaction_id = connection.execute(sqlalchemy.text(
            "INSERT INTO transactions (description) \
            VALUES (CONCAT('adding :quantity ', :sku, ' to cart :cart_id')) \
            RETURNING id"),
             {"quantity": cart_item.quantity,
              "sku": item_sku,
              "cart_id": cart_id}).first()[0]
        connection.execute(sqlalchemy.text(
            "INSERT INTO potions_ledger (potion_id, potion_transaction_id, change) \
            SELECT potion_id, :transaction_id, :change \
            FROM ( \
            SELECT * \
            FROM catalog_items \
            JOIN potions_ledger ON catalog_items.id = potions_ledger.potion_id \
            ) AS potions \
            WHERE sku = :sku \
            GROUP BY potion_id"),
            {"transaction_id": transaction_id,
             "change": -cart_item.quantity,
             "sku": item_sku})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT cart_items.quantity, catalog_items.price \
                                    FROM cart_items \
                                    JOIN carts on cart_items.cart = carts.id \
                                    JOIN catalog_items on cart_items.item_id = catalog_items.id \
                                    WHERE cart = :cart"), 
                                    {"cart" : cart_id}).fetchall()
        potions_bought = 0
        gold_spent = 0
        for row in result:
            potions_bought += row[0]
            gold_spent += row[1] * row[0]
        result = connection.execute(sqlalchemy.text("UPDATE carts \
                                                    SET checked_out = true \
                                                    WHERE id=:cart"),
                                                    {"cart": cart_id})
        transaction_id = connection.execute(sqlalchemy.text(
            "INSERT INTO transactions (description) \
            VALUES ('cart :cart_id checks out :potions_bought potions for :gold_spent gold') \
            RETURNING id"), 
            {"cart_id": cart_id, "potions_bought": potions_bought, "gold_spent": gold_spent}
        ).first()[0]
        connection.execute(sqlalchemy.text(
            "INSERT INTO gold_ledger (gold_transaction_id, change) \
            VALUES \
            (:transaction_id, :price) \
            RETURNING id"), 
            {"price": gold_spent, "transaction_id": transaction_id}
        )
    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_spent}
