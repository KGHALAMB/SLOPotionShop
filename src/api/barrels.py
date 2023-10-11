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
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    price = 0
    for row in barrels_delivered:
        if row.sku == "SMALL_RED_BARREL":
            price += row.price * row.quantity
            red_ml += row.ml_per_barrel * row.quantity
        if row.sku == "SMALL_BLUE_BARREL":
            price += row.price * row.quantity
            blue_ml += row.ml_per_barrel * row.quantity
        if row.sku == "SMALL_GREEN_BARREL":
            price += row.price * row.quantity
            green_ml += row.ml_per_barrel * row.quantity
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(red_ml) +
                                                    ", num_blue_ml = num_blue_ml + " + str(blue_ml) +  
                                                    ", num_green_ml = num_green_ml + " + str(green_ml) + 
                                                    ", gold = gold - " + str(price)))
    print(barrels_delivered)
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    result = []
    gold_spent = 0
    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
    
    for barrel in wholesale_catalog:
        if barrel.quantity > 0:
            if barrel.sku == "SMALL_RED_BARREL":
                red_price = barrel.price
                with db.engine.begin() as connection:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
                if num_potions.first()[0] < 5 and gold-gold_spent >= red_price:
                    barrel.quantity = 1
                    gold_spent += red_price
                    result.append(barrel)
            if barrel.sku == "SMALL_GREEN_BARREL":
                green_price = barrel.price
                with db.engine.begin() as connection:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
                if num_potions.first()[0] < 5 and gold-gold_spent >= green_price:
                    barrel.quantity = 1
                    gold_spent += green_price
                    result.append(barrel)
            if barrel.sku == "SMALL_BLUE_BARREL":
                blue_price = barrel.price
                with db.engine.begin() as connection:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory"))
                if num_potions.first()[0] < 5 and gold-gold_spent >= blue_price:
                    gold_spent += blue_price
                    barrel.quantity = 1
                    result.append(barrel)
        if gold_spent >= gold:
            return result
    return result
