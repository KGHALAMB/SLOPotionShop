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
        #make transaction id
        transaction_id = connection.execute(sqlalchemy.text(
                                        "INSERT INTO transactions (description) \
                                        VALUES ('bottler delivered potions') \
                                        RETURNING id"
                                        )).first()[0]
        for row in potions_delivered:            
            # make ml ledger
            if row.quantity > 0:
                connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (color, ml_transaction_id, change) \
                                                    VALUES \
                                                    ('red', :transaction_id, :red_quantity), \
                                                    ('blue', :transaction_id, :blue_quantity), \
                                                    ('green', :transaction_id, :green_quantity)"),
                                                    {"transaction_id" : transaction_id,
                                                    "red_quantity" : -row.potion_type[0] * row.quantity,
                                                    "green_quantity" : -row.potion_type[1] * row.quantity,
                                                    "blue_quantity" : -row.potion_type[2] * row.quantity})
                #get potion id
                potion_id = connection.execute(sqlalchemy.text(
                    "SELECT id \
                    FROM catalog_items \
                    WHERE red_ml = :red and green_ml = :green and blue_ml = :blue and dark_ml = 0"),
                    {"red": row.potion_type[0],
                    "green": row.potion_type[1],
                    "blue": row.potion_type[2]}).first()[0]
                # make potion ledger
                connection.execute(sqlalchemy.text("INSERT INTO potions_ledger (potion_id, potion_transaction_id, change) \
                                                    VALUES \
                                                    (':id', :transaction_id, :quantity)"),
                                                    {"id": potion_id,
                                                    "transaction_id" : transaction_id,
                                                    "quantity" : row.quantity})
                                                
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    potions ={}
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT name, red_ml, green_ml, blue_ml, dark_ml, id FROM catalog_items"))
        for row in result:
            print(row)
            quantity = connection.execute(sqlalchemy.text(
                "SELECT sum(change) FROM potions_ledger WHERE potion_id = :potion_id"),
                {"potion_id": row[5]}).first()[0]
            potions[row[0]] =  {"quantity" : quantity, "recipe" : [row[1], row[2], row[3], row[4]], "amt_added" : 0}
        sorted_potions = dict(sorted(potions.items(), key=lambda item: item[1]["quantity"]))
        red_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) \
                                                    FROM ml_ledger \
                                                    WHERE color = 'red'")).first()[0]
        green_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) \
                                                    FROM ml_ledger \
                                                    WHERE color = 'green'")).first()[0]
        blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) \
                                                    FROM ml_ledger \
                                                    WHERE color = 'blue'")).first()[0]
        full_inventory = connection.execute(sqlalchemy.text(
                "SELECT sum(change) FROM potions_ledger")).first()[0]
        tot_added = 0
        ml_stock = [red_ml, green_ml, blue_ml, 0]
        for key, value in sorted_potions.items():
            if tot_added == 300 - full_inventory:
                break
            if red_ml >= value["recipe"][0] and green_ml >= value["recipe"][1] and blue_ml >= value["recipe"][2]:
                max_potions = [0, 0, 0, 0] 
                for i in range(0, len(max_potions)):
                    if value["recipe"][i] > 0:
                        max_potions[i] += ml_stock[i] // value["recipe"][i]
                    else:
                        max_potions[i] = float('inf')
                added_pots = min(max_potions)
                if added_pots > 300 - full_inventory:
                    added_pots = 300 - full_inventory
                value["amt_added"] += added_pots
                tot_added += added_pots
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
