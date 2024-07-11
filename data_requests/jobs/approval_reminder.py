import logging
from datetime import timedelta

import dateutil.tz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils import timezone

from data_requests.models import DataRequest, RequestState
from notifications.views import RequestNotificationCreateView

logger = logging.getLogger(__name__)
SCHEDULER = BackgroundScheduler()


def is_reminder_due(request_state: RequestState):
    return timezone.now() - request_state.created_on > timedelta(days=3 * (request_state.reminders_count + 1))


def approval_reminder():
    logger.info("Starting approval reminder job...")
    data_requests = DataRequest.objects.all()
    for data_request in data_requests:
        request_states = RequestState.objects.filter(request_id=data_request.request_id).prefetch_related(
            'state_lookup')
        for request_state in request_states:
            if request_state.state_lookup.state == "Unattended":
                logger.info("Found unattended request for state {}".format(request_state.created_on))
                logger.info("Current: {} \n| request: {}".format(timezone.now(), request_state.created_on))
                if is_reminder_due(request_state):
                    try:
                        logger.info("Reminding request for {}".format(data_request.title))
                        (RequestNotificationCreateView
                         .create_request_notification(request_state.request_state_id,
                                                      f'The request titled "{data_request.title}" is overdue and '
                                                      f'awaiting your review/approval.'))
                    except Exception as e:
                        logger.error(f"Error while reminding request for {data_request.title}: {str(e)}")
                else:
                    logger.info("Still have time for request state {}".format(request_state.created_on))


def start():
    trigger = CronTrigger(day_of_week="mon-fri", hour=8)
    SCHEDULER.add_job(approval_reminder, trigger=trigger)
    SCHEDULER.start()
