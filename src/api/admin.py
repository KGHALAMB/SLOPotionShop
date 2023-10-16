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
        result = connection.execute(sqlalchemy.text("UPDATE catalog_items SET quantity = 0"))
        
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET \
                                                    num_red_potions = 0, num_red_ml = 0, \
                                                    num_green_potions = 0, num_green_ml = 0, \
                                                    num_blue_potions = 0, num_blue_ml = 0, \
                                                     gold = 100"))
        result = connection.execute(sqlalchemy.text("DELETE FROM carts"))
        result = connection.execute(sqlalchemy.text("DELETE FROM cart_items"))
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Potion Shop",
        "shop_owner": "Potion Seller",
    }

