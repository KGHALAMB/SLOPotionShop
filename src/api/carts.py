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
        result = connection.execute(sqlalchemy.text("UPDATE catalog_items \
                                                    SET quantity = quantity - :quantity \
                                                    WHERE sku = :item_sku"),
                                                    {"quantity": cart_item.quantity,
                                                     "item_sku": item_sku})
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
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory \
                                                    SET gold = gold + :gold"),
                                                    {"gold": gold_spent})
    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_spent}
