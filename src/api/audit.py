import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    with db.engine.begin() as connection:
        number_of_potions = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM potions_ledger")).first()[0]
        ml_in_barrels = connection.execute(sqlalchemy.text("SELECT SUM(change) from ml_ledger")).first()[0]
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change) from gold_ledger")).first()[0]
    return {"number_of_potions": number_of_potions, "ml_in_barrels": ml_in_barrels, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
