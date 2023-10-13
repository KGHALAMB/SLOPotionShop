import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_blue_potions, num_green_potions FROM global_inventory"))
        for row in num_potions:                
            num_red = row[0]
            num_blue = row[1]
            num_green = row[2]
        res = []
        if num_red > 0:
            res.append({
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_red,
                "price": 50,
                "potion_type": [100, 0, 0, 0]
            })
        if num_green > 0:
            res.append({
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green,
                "price": 50,
                "potion_type": [0, 100, 0, 0]
            })
        if num_blue > 0:
            res.append({
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": num_blue,
                "price": 50,
                "potion_type": [0, 0, 100, 0]
            })
        return res

    
    # Can return a max of 20 items.

    
