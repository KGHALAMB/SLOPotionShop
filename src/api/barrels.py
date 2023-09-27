import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    ml = 0
    price = 0
    for row in barrels_delivered:
        price += row.price * row.quantity
        ml += row.ml_per_barrel * row.quantity
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(ml) + ", gold = gold - " + str(price)))
    print(barrels_delivered)
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    for barrel in wholesale_catalog:
        if barrel.sku == "SMALL_RED_BARREL":
            price = barrel.price
            ml_per_barrel = barrel.ml_per_barrel
            potion_type = barrel.potion_type
    print(wholesale_catalog)
    quantity = 0
    with db.engine.begin() as connection:
        num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        if num_potions.first()[0] < 10 and gold.first()[0] >= price:
            quantity = 1
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "ml_per_barrel": ml_per_barrel,
            "potion_type": potion_type,
            "price": price,
            "quantity": quantity
        }
    ]
