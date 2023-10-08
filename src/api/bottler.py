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
    red_quantity = 0
    green_quantity = 0
    blue_quantity = 0
    for row in potions_delivered:
        if row.potion_type == [100, 0, 0, 0]:
            red_quantity += row.quantity
        elif row.potion_type == [0, 100, 0, 0]:
            green_quantity += row.quantity
        elif row.potion_type == [0, 0, 100, 0]:
            blue_quantity += row.quantity
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions + " + str(red_quantity) + 
                                                    ", num_red_ml = num_red_ml - " + str(100 * red_quantity) + 
                                                    ", num_green_potions = num_green_potions + " + str(green_quantity) + 
                                                    ", num_green_ml = num_green_ml - " +  str(100 * green_quantity) +
                                                    ", num_blue_potions = num_blue_potions + " + str(blue_quantity) + 
                                                    ", num_blue_ml = num_blue_ml - " + str(100 * blue_quantity)))
    
    print(potions_delivered)

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    red_quantity = 0
    blue_quantity = 0
    green_quantity = 0

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"))
        for row in result:
            red_ml = row[0]
            green_ml = row[1]
            blue_ml = row[2]
        if red_ml >= 100:
            red_quantity = red_ml // 100
        if green_ml >= 100:
            green_quantity = green_ml // 100
        if blue_ml >= 100:
            blue_quantity = blue_ml // 100
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": red_quantity
            },
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": green_quantity
            },
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": blue_quantity
            }
        ]
