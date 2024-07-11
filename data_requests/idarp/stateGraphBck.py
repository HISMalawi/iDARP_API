# from state import State
# from nextState import NextState
from collections import deque
import mysql.connector as mysql
import json


class StatesGraph:
    branch = 0
    mergers = deque([])
    visited = []

    def __init__(self) -> None:
        pass

    @classmethod
    def connectDB(cls):
        db = mysql.connect(
            host="34.71.119.33",
            user="admin",
            passwd="Very*secure",
            database="dev_test"
        )
        return db

    @classmethod
    def createGraph(cls, request_id, params):
        pass

    @classmethod
    def getOrgRole(cls, role_id):
        return None

    @classmethod
    def getStage(cls, id):
        db = StatesGraph.connectDB()
        cursor = db.cursor()

        def get_stage(id):
            nonlocal db
            nonlocal cursor
            sql = f"select * from v_approval_procedure_stages where stage_id = {id}"
            cursor.execute(sql)
            res = cursor.fetchall()
            stage = {"stage_id": res[0][1], "stage_order": res[0][2], "stage_activity": res[0][4],
                     "branch_level": res[0][5], "stage_type": res[0][3], "role": res[0][8], "org_role_id": res[0][7],
                     "pos_x": float(res[0][9]), "pos_y": float(res[0][10]), "icon": res[0][11], "next": []}
            # stage["org_role"] = StatesGraph.getOrgRole(1)
            sql = f"select * from next_stages where current_stage_id = {stage['stage_id']}"
            cursor.execute(sql)
            next = cursor.fetchall()

            if stage["stage_type"] == "Junction":
                StatesGraph.branch += 1
            elif stage["stage_type"] == "Merge":
                StatesGraph.branch -= 1

            if id not in StatesGraph.visited:
                for n in next:
                    print(n)
                    stage['next'].append(get_stage(n[2]))
            StatesGraph.visited.append(id)
            return stage

        stages = get_stage(id)
        db.close()
        return stages

    @classmethod
    def createStatesGraph(cls, requestId, current):
        db = StatesGraph.connectDB()
        cursor = db.cursor()

        def createState(requestId, current):
            nonlocal db
            nonlocal cursor
            state_lookup_id = 2
            reason = None
            if current['stage_type'] == "Initial":
                state_lookup_id = 1
                reason = "Interested in data"
            sql = f"INSERT INTO request_state (state_lookup_id, reason, org_role_id, request_id, branch_level, stage_order, stage_type, pos_x, pos_y, icon, reminders_count) \
                values({state_lookup_id}, '{reason}', {current['org_role_id']}, {requestId}, '{current['branch_level']}', '{current['stage_order']}', '{current['stage_type']}', '{current['pos_x']}', '{current['pos_y']}', '{current['icon']}', 0)"
            cursor.execute(sql)
            state_id = cursor.lastrowid
            for next in current['next']:
                next_state_id = createState(requestId, next)
                sql = f"INSERT INTO next_state (current_state_id, next_id) values({state_id}, {next_state_id})"
                cursor.execute(sql)
            return state_id

        createState(requestId, current)
        db.commit()
        db.close()


if __name__ == "__main__":
    StatesGraph.createStatesGraph(52, StatesGraph.getStage(1))
