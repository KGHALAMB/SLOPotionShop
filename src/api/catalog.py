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
        num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory"))
        num_potions = num_potions.first()[0]
        if num_potions > 0:
            return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]
        return []

    
    # Can return a max of 20 items.

    
