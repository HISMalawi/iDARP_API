class State:
    def __init__(self) -> None:
        pass
    
    @classmethod
    def createState(cls,params):
        ##### Create State #####

        ##### Save state_id #####
        state_id = 0

        ##### Create all outgoing edges #####

        ##### Return state_id #####
        return state_id

class NextState:
    def __init__(self) -> None:
        pass
    
    @classmethod
    def createNext(self, current, nextParams):
        next_id = State.createState(nextParams)
        ######## use the next_id and the passed current param to insert Next_State instance in db ########

        #### Return id of 
        return next_id

class StatesGraph:
    def __init__(self) -> None:
        pass

