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

    red_quantity = 0
    green_quantity = 0
    blue_quantity = 0

    for barrel in wholesale_catalog:
        if barrel.quantity > 0:
            if barrel.sku == "SMALL_RED_BARREL":
                red_price = barrel.price
                red_ml_per_barrel = barrel.ml_per_barrel
                red_potion_type = barrel.potion_type
                with db.engine.begin() as connection:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
                    gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
                    if num_potions.first()[0] < 10 and gold.first()[0] >= green_price:
                        red_quantity = 1
                        result.append({
                                "sku": "SMALL_RED_BARREL",
                                "ml_per_barrel": red_ml_per_barrel,
                                "potion_type": red_potion_type,
                                "price": red_price,
                                "quantity": red_quantity
                            })
            if barrel.sku == "SMALL_GREEN_BARREL":
                green_price = barrel.price
                green_ml_per_barrel = barrel.ml_per_barrel
                green_potion_type = barrel.potion_type
                with db.engine.begin() as connection:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
                    gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
                if num_potions.first()[0] < 10 and gold.first()[0] >= green_price:
                    green_quantity = 1
                    result.append({
                        "sku": "SMALL_GREEN_BARREL",
                        "ml_per_barrel": green_ml_per_barrel,
                        "potion_type": green_potion_type,
                        "price": green_price,
                        "quantity": green_quantity
                    })
            if barrel.sku == "SMALL_BLUE_BARREL":
                blue_price = barrel.price
                blue_ml_per_barrel = barrel.ml_per_barrel
                blue_potion_type = barrel.potion_type
                with db.engine.begin() as connection:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory"))
                    gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
                    if num_potions.first()[0] < 10 and gold.first()[0] >= blue_price:
                        blue_quantity = 1
                        result.append({
                        "sku": "SMALL_BLUE_BARREL",
                        "ml_per_barrel": blue_ml_per_barrel,
                        "potion_type": blue_potion_type,
                        "price": blue_price,
                        "quantity": blue_quantity
                        })
        print(wholesale_catalog)
    
    return result
