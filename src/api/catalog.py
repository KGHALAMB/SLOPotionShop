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
        result = connection.execute(sqlalchemy.text("SELECT sku, name, SUM(change) AS quantity, price, red_ml, green_ml, blue_ml, dark_ml \
                                                    FROM ( \
                                                    SELECT * \
                                                    FROM catalog_items \
                                                    JOIN potions_ledger ON catalog_items.id = potions_ledger.potion_id \
                                                    ) AS potions \
                                                    GROUP BY sku, name, price, red_ml, green_ml, blue_ml, dark_ml \
                                                    ORDER BY quantity DESC \
                                                    LIMIT 6")).fetchall()
        
        res = []
        print(result)
        for row in result:
            if row[2] > 0:
                res.append({
                    "sku": row[0],
                    "name": row[1],
                    "quantity": row[2],
                    "price": row[3],
                    "potion_type": [row[4], row[5], row[6], row[7]]
                })
        return res

    
    # Can return a max of 6 items.

    
