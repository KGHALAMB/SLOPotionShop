import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import random


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
        print("the barrel is ", row, row.price, row.quantity)
        if row.sku == "SMALL_RED_BARREL" or row.sku == "MEDIUM_RED_BARREL" or row.sku == "MINI_RED_BARREL" or row.sku == "LARGE_RED_BARREL":
            price += row.price * row.quantity
            red_ml += row.ml_per_barrel * row.quantity
        elif row.sku == "SMALL_BLUE_BARREL" or row.sku ==  "MEDIUM_BLUE_BARREL" or row.sku == "MINI_BLUE_BARREL" or row.sku == "LARGE_BLUE_BARREL":
            price += row.price * row.quantity
            blue_ml += row.ml_per_barrel * row.quantity
        elif row.sku == "SMALL_GREEN_BARREL" or row.sku ==  "MEDIUM_GREEN _BARREL" or row.sku == "MINI_GREEN_BARREL" or row.sku == "LARGE_GREEN_BARREL":
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
    
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        gold_spent = 0
        stock = {}
        result = connection.execute(sqlalchemy.text(
            "SELECT num_red_ml, num_green_ml, num_blue_ml, gold \
            FROM global_inventory"
        )).first()
        stock["RED_BARREL"], stock["GREEN_BARREL"], stock["BLUE_BARREL"] = result[0], result[1], result[2]
        gold = result[3]
        print(stock)
        sorted_stock = dict(sorted(stock.items(), key=lambda item: item[1]))
        print(sorted_stock.items())
        res = []
        for key, value in sorted_stock.items():
                for barrel in wholesale_catalog:
                    if barrel.quantity > 0 and barrel.sku == "LARGE_"+key and gold - gold_spent >= barrel.price:
                        newBarrel = barrel
                        newBarrel.quantity = 1
                        res.append({"sku": barrel.sku,
                                    "ml_per_barrel": barrel.ml_per_barrel,
                                    "potion_type": barrel.potion_type,
                                    "price": barrel.price,
                                    "quantity": 1})
                        barrel.quantity -= 1
                        gold_spent += barrel.price
                    if barrel.quantity > 0 and barrel.sku == "MEDIUM_"+key and gold - gold_spent >= barrel.price:
                        newBarrel = barrel
                        newBarrel.quantity = 1
                        res.append({"sku": barrel.sku,
                                    "ml_per_barrel": barrel.ml_per_barrel,
                                    "potion_type": barrel.potion_type,
                                    "price": barrel.price,
                                    "quantity": 1})
                        barrel.quantity -= 1
                        gold_spent += barrel.price
                    elif barrel.quantity > 0 and barrel.sku == "SMALL_"+key and  gold - gold_spent >= barrel.price:
                        newBarrel = barrel
                        newBarrel.quantity = 1
                        print(newBarrel)
                        res.append({"sku": barrel.sku,
                                    "ml_per_barrel": barrel.ml_per_barrel,
                                    "potion_type": barrel.potion_type,
                                    "price": barrel.price,
                                    "quantity": 1})                        
                        barrel.quantity -= 1
                        gold_spent += barrel.price         
                    elif barrel.quantity > 0 and barrel.sku == "MINI_"+key and  gold - gold_spent >= barrel.price:
                        newBarrel = barrel
                        newBarrel.quantity = 1
                        print(newBarrel)
                        res.append({"sku": barrel.sku,
                                    "ml_per_barrel": barrel.ml_per_barrel,
                                    "potion_type": barrel.potion_type,
                                    "price": barrel.price,
                                    "quantity": 1})                        
                        barrel.quantity -= 1
                        gold_spent += barrel.price
                print(res)
        return res
                
        """gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first()[0]
        for barrel in wholesale_catalog:
            if barrel.quantity > 0:
                if barrel.sku == "SMALL_RED_BARREL":
                    red_price = barrel.price
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
                    if num_potions.first()[0] < 5 and gold-gold_spent >= red_price:
                        barrel.quantity = 1
                        gold_spent += red_price
                        result.append(barrel)
                if barrel.sku == "SMALL_GREEN_BARREL":
                    green_price = barrel.price
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
                    if num_potions.first()[0] < 5 and gold-gold_spent >= green_price:
                        barrel.quantity = 1
                        gold_spent += green_price
                        result.append(barrel)
                if barrel.sku == "SMALL_BLUE_BARREL":
                    blue_price = barrel.price
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory"))
                    if num_potions.first()[0] < 5 and gold-gold_spent >= blue_price:
                        gold_spent += blue_price
                        barrel.quantity = 1
                        result.append(barrel)
            if gold_spent >= gold:
                return result"""