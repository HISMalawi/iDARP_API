import logging
from collections import deque
from data_requests.models import RequestState, NextState, Stage, NextStage
from users.models import OrgRoleStatus
from django.db.models import F, Max, Q, OuterRef, Subquery

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class StatesGraph:
    branch = 0
    merger_ids = deque()

    @classmethod
    def getStage(cls, id, visited):
        def get_stage(id, visited):

            activeOrgRoleQueryset = OrgRoleStatus.objects.select_related('org_role').values(
                'org_role_id',
                'status',
                'changed_on',
            ).annotate(
                role=F('org_role__role__role'),
                role_id=F('org_role__role__role_id'),
                org_id=F('org_role__org_id'),
                org_name=F('org_role__org__name')
            )
            approvalProcedureStageQueryset = Stage.objects.select_related(
                'approval_procedure',
                'role',
                'stage_type'
            ).filter(approval_procedure_id=1, stage_id=id).values(
                'stage_id',
                'stage_order',
                'role_id',
                'stage_activity',
                'branch_level',
                'pos_x',
                'pos_y',
                'icon'
            ).annotate(
                stage_type=F('stage_type__stage_type')
            ).order_by('stage_order')

            inner_join_queryset = approvalProcedureStageQueryset.annotate(
                role=Subquery(activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('role')[:1]),
                # I don't like the fact that this subquery is repeated
                org_role_id=Subquery(
                    activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('org_role_id')[:1]),
                # but at the time of coding this I didn't have much choice
                org_name=Subquery(activeOrgRoleQueryset.filter(role_id=OuterRef('role_id')).values('org_name')[:1])
                # as returning more than 1 columns from a subquery cauzed errors
            ).order_by('stage_order')

            stage = list(inner_join_queryset)[0]

            # logger.debug(f"+++++++++{stage}")
            
            if stage:
                next_stages = NextStage.objects.filter(current_stage_id=id).values('next_id')

                stage['stage_type'] = stage.pop('stage_type')
                stage['org_role_id'] = stage.pop('role_id')
                stage['role'] = stage.pop('role')
                stage['next'] = []

                if stage['stage_type'] == "Junction":
                    StatesGraph.branch += 1
                elif stage['stage_type'] == "Merge":
                    StatesGraph.branch -= 1

                if id not in visited:
                    for n in next_stages:
                        next_id = n['next_id']
                        stage['next'].append(get_stage(next_id, visited))

                    visited.add(id)

            return stage

        stages = get_stage(id, visited)
        return stages

    @classmethod
    def createStatesGraph(cls, requestId, current, visited):
        state_lookup_id = 2
        reason = None

        if current['stage_type'] == "Initial":
            state_lookup_id = 1

        if current['stage_type'] == "Junction":
            StatesGraph.branch += 1
        elif current['stage_type'] == "Merge":
            StatesGraph.branch -= 1

        logger.debug(f"++++{current}")
        if current['stage_type'] == "Merge":
            state_id = None
            if len(StatesGraph.merger_ids) > 0:
                state_id = StatesGraph.merger_ids.pop()
            else:
                state = RequestState.objects.create(
                    state_lookup_id=state_lookup_id,
                    reason=reason,
                    org_role_id=current['org_role_id'],
                    request_id=requestId,
                    branch_level=current['branch_level'],
                    stage_order=current['stage_order'],
                    stage_type=current['stage_type'],
                    pos_x=current['pos_x'],
                    pos_y=current['pos_y'],
                    icon=current['icon'],
                    reminders_count=0
                )
                state_id = state.pk

            for next_stage in current['next']:
                next_state_id = StatesGraph.createStatesGraph(requestId, next_stage, visited)
                NextState.objects.create(current_state_id=state_id, next_id=next_state_id)

        else:
            state = RequestState.objects.create(
                state_lookup_id=state_lookup_id,
                reason=reason,
                org_role_id=current['org_role_id'],
                request_id=requestId,
                branch_level=current['branch_level'],
                stage_order=current['stage_order'],
                stage_type=current['stage_type'],
                pos_x=current['pos_x'],
                pos_y=current['pos_y'],
                icon=current['icon'],
                reminders_count=0
            )
            state_id = state.pk

            for next_stage in current['next']:
                next_state_id = StatesGraph.createStatesGraph(requestId, next_stage, visited)
                NextState.objects.create(current_state_id=state_id, next_id=next_state_id)

        return state_id

if __name__ == "__main__":
    # Modify these values accordingly
    request_id = 214
    initial_stage_id = 1

    initial_stage = StatesGraph.getStage(initial_stage_id, set())  # Pass an empty set for visited
    if initial_stage:
        StatesGraph.createStatesGraph(request_id, initial_stage, set())  # Pass an empty set for visited
