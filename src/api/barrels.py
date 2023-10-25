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
    print(barrels_delivered)
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
        elif row.sku == "SMALL_GREEN_BARREL" or row.sku ==  "MEDIUM_GREEN_BARREL" or row.sku == "MINI_GREEN_BARREL" or row.sku == "LARGE_GREEN_BARREL":
            price += row.price * row.quantity
            green_ml += row.ml_per_barrel * row.quantity
    with db.engine.begin() as connection:
        # record transaction
        transaction_id = connection.execute(sqlalchemy.text(
            "INSERT INTO transactions (description) \
            VALUES (':red_ml ml to red, :green_ml to green, :blue_ml to blue, paid :price gold') \
            RETURNING id"), 
            {"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "price": price}
        ).first()[0]
        # add to the ml ledger 
        connection.execute(sqlalchemy.text(
            "INSERT INTO ml_ledger (color, ml_transaction_id, change) \
            VALUES \
            ('red', :transaction_id, :red_ml), \
            ('green', :transaction_id, :green_ml), \
            ('blue', :transaction_id, :blue_ml) \
            RETURNING id"), 
            {"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "transaction_id": transaction_id}
        )
        # add to the gold ledger
        connection.execute(sqlalchemy.text(
            "INSERT INTO gold_ledger (gold_transaction_id, change) \
            VALUES \
            (:transaction_id, :price) \
            RETURNING id"), 
            {"price": -price, "transaction_id": transaction_id}
        )
    print(barrels_delivered)
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        gold_spent = 0
        stock = {}
        red_ml = connection.execute(sqlalchemy.text(
            "SELECT SUM(change) FROM ml_ledger WHERE color = 'red'"   
        )).first()[0]
        green_ml = connection.execute(sqlalchemy.text(
            "SELECT SUM(change) FROM ml_ledger WHERE color = 'green'"   
        )).first()[0]
        blue_ml = connection.execute(sqlalchemy.text(
            "SELECT SUM(change) FROM ml_ledger WHERE color = 'blue'"   
        )).first()[0]
        gold = connection.execute(sqlalchemy.text(
            "SELECT SUM(change) FROM gold_ledger"   
        )).first()[0]
        if(sum([red_ml, green_ml, blue_ml]) == 0):
            color = ["RED_BARREL", "GREEN_BARREL", "BLUE_BARREL"]
            random.shuffle(color)
            sorted_stock = {color[0]: 0, color[1]: 0, color[2]: 0}
        else:
            stock["RED_BARREL"], stock["GREEN_BARREL"], stock["BLUE_BARREL"] = red_ml, green_ml, blue_ml
            sorted_stock = dict(sorted(stock.items(), key=lambda item: item[1]))      
        res = []
        print(sorted_stock)
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
                    elif barrel.quantity > 0 and barrel.sku == "MEDIUM_"+key and gold - gold_spent >= barrel.price:
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
                        res.append({"sku": barrel.sku,
                                    "ml_per_barrel": barrel.ml_per_barrel,
                                    "potion_type": barrel.potion_type,
                                    "price": barrel.price,
                                    "quantity": 1})                        
                        barrel.quantity -= 1
                        gold_spent += barrel.price
        return res
                