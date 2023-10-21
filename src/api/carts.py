import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts DEFAULT VALUES RETURNING id")).first()[0]
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
        result = connection.execute(sqlalchemy.text("DELETE FROM carts \
                                                    WHERE id = :cart"),
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
