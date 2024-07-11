from .state import State
from .dbconnect import connectDB

class NextState:
    def __init__(self, ) -> None:
        self.stage_id = None
    
    @classmethod
    def createNext(self, current, nextParams):
        db = connectDB()
        cursor = db.cursor()
        next_id = State.createState(nextParams)
        sql = f"insert into next_state ()"
        ######## use the next_id and the passed current param to insert Next_State instance in db ########

        #### Return id of 
        return next_id