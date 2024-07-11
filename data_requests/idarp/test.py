import logging
from collections import deque
from data_requests.models import RequestState, NextState, Stage, NextStage
from users.models import OrgRoleStatus
from django.db.models import F, Value, IntegerField

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Test:
    @classmethod
    def get_test(cls):
        active_org_roles = OrgRoleStatus.objects.select_related('org_role').filter(status=1).values(
            'status',
            'changed_on',
            'org_role__org_role_id',
            'org_role__org_id',
            'org_role__org__name',
            'org_role__role__role',
            'org_role__role_id',
        )

        # Query to create the view equivalent using joins and filters
        approval_procedure_stages = Stage.objects.select_related(
            'stage_type',
            'approval_procedure'
        ).filter(
            approval_procedure_id=1,
            role__in=active_org_roles.values_list('org_role__role_id', flat=True)
        ).order_by('stage_order')

        logger.debug(f"++++++++++++++ {approval_procedure_stages}")
