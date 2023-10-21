from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
 
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("DELETE FROM potions_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM gold_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM ml_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM transactions"))
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (description) \
                                                            VALUES ('initializing all values') \
                                                            RETURNING id")).first()[0]
        connection.execute(sqlalchemy.text("INSERT INTO potions_ledger (potion_id, potion_transaction_id, change) \
                                            SELECT id, :transaction_id, 0 \
                                            FROM catalog_items"),
                                           {"transaction_id": transaction_id})
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (gold_transaction_id, change)\
                                           VALUES \
                                           (:transaction_id, 100)"),
                                           {"transaction_id": transaction_id})
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (color, ml_transaction_id, change) \
                                           VALUES \
                                           ('red', :transaction_id, 0), \
                                           ('green', :transaction_id, 0), \
                                           ('blue', :transaction_id, 0)"),
                                           {"transaction_id": transaction_id})
        connection.execute(sqlalchemy.text("DELETE FROM carts"))
        connection.execute(sqlalchemy.text("DELETE FROM cart_items"))
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Potion Shop",
        "shop_owner": "Potion Seller",
    }

