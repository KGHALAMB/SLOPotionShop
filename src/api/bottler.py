import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    with db.engine.begin() as connection:
        for row in potions_delivered:
            result = connection.execute(sqlalchemy.text("UPDATE catalog_items " \
                                        "SET quantity = quantity + :amt_added " \
                                        "WHERE red_ml = :red_ml and blue_ml = :blue_ml and green_ml = :green_ml"), 
                                        {"amt_added" : row.quantity,
                                         "red_ml" : row.potion_type[0],
                                          "green_ml" : row.potion_type[1],
                                          "blue_ml" : row.potion_type[2]})
            result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET " \
                                                        "num_red_ml = num_red_ml - :amt_used_red, " \
                                                        "num_green_ml = num_green_ml - :amt_used_green, " \
                                                        "num_blue_ml = num_blue_ml - :amt_used_blue"),
                                                        {"amt_used_red" : row.potion_type[0] * row.quantity,
                                                         "amt_used_green" : row.potion_type[1] * row.quantity,
                                                         "amt_used_blue" : row.potion_type[2] * row.quantity})
            
                                                         
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    potions ={}
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT name, quantity, red_ml, green_ml, blue_ml, dark_ml FROM catalog_items"))
        for row in result:
            potions[row[0]] =  {"quantity" : row[1], "recipe" : [row[2], row[3], row[4], row[5]], "amt_added" : 0}
        sorted_potions = dict(sorted(potions.items(), key=lambda item: item[1]["quantity"]))
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"))
        for row in result:
            red_ml = row[0]
            green_ml = row[1]
            blue_ml = row[2]
        ml_stock = [red_ml, green_ml, blue_ml, 0]
        for key, value in sorted_potions.items():
            if red_ml >= value["recipe"][0] and green_ml >= value["recipe"][1] and blue_ml >= value["recipe"][2]:
                max_potions = [0, 0, 0, 0] 
                for i in range(0, len(max_potions)):
                    if value["recipe"][i] > 0:
                        max_potions[i] += ml_stock[i] // value["recipe"][i]
                    else:
                        max_potions[i] = float('inf')
                added_pots = min(max_potions)
                value["amt_added"] += added_pots
                for i in range(0, len(ml_stock)):
                    ml_stock[i] -= added_pots * value["recipe"][i]
                    print(value)
                    print(ml_stock, added_pots * value["recipe"][i])
        result = []
        for row in sorted_potions:
            result.append({"potion_type": sorted_potions[row]["recipe"],
                           "quantity": sorted_potions[row]["amt_added"]})
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    return result
