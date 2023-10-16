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
        result = connection.execute(sqlalchemy.text("SELECT sku, name, quantity, price, red_ml, green_ml, blue_ml, dark_ml \
                                                    FROM catalog_items")).fetchall()
        res = []
        print(result)
        total = 0
        for row in result:
            if row[2] > 0 and total + row[2] <= 20:
                res.append({
                    "sku": row[0],
                    "name": row[1],
                    "quantity": row[2],
                    "price": row[3],
                    "potion_type": [row[4], row[5], row[6], row[7]]
                })
                total += row[2]
            elif total + row[2] > 20 and total != 20:
                res.append({
                    "sku": row[0],
                    "name": row[1],
                    "quantity": 20 - total,
                    "price": row[3],
                    "potion_type": [row[4], row[5], row[6], row[7]]
                })
                total += 20 - total
        return res

    
    # Can return a max of 20 items.

    
