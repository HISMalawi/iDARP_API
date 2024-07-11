from .dbconnect import connectDB
from .nextState import NextState

class State:
    def __init__(self) -> None:
        self.state_id = None
        self.next_states = []
    
    @classmethod
    def createState(cls,params):
        next_states = []
        ##### Create State #####

        ##### Save state_id #####
        state_id = 0

        ##### Create all outgoing edges #####
        for edge in next_states:
            NextState.createNext(state_id, params)
        ##### Return state_id #####
        return state_id