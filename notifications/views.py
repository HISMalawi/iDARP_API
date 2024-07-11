import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import F
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from main.utils.mail_sender import MailSender

from data_requests.models import NextState, RequestState
from notifications.constants import APPROVED_STATUS, DATA_REQUESTER_ROLE, DENIED_STATUS, DATA_SECURITY_APPROVER_ROLE, \
    DATA_ACCESS_APPROVER_ROLE, DATA_CUSTODIAN_ROLE, DATA_OFFICER_ROLE
from notifications.models import Notification, RequestNotification, GroupNotification, UserNotification
from notifications.serializers import NotificationSerializer, RequestNotificationSerializer
from users.models import OrgRole, AssignedRole

logger = logging.getLogger(__name__)


class SendNotification(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_id = request.data['user_id']
        notification = request.data['notification']
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications-{user_id}',
            {
                'type': 'send_notification',
                'data': {

                    "notification_id": 123456789,
                    "subject": "Test Notification",
                    "description": "string",
                    "is_read": False,
                }
            }
        )
        return Response({'code': '200', 'message': 'Notification sent successfully.'}, status=status.HTTP_200_OK)


class NotificationCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        instance = self.create(request, *args, **kwargs)
        notificationId = instance.data['notification_id']  # will use in the creation of request notifications
        notificationType = instance.data['notification_type']  # will use in the creation of request notifications
        return instance


class GetUserNotifications(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        notifications = self.get_all_user_notifications(user_id)
        return Response(notifications, status=status.HTTP_200_OK)

    @classmethod
    def get_users_ids(cls, user_id):
        queryset = OrgRole.objects.all().filter(assignedrole__user_id=user_id,
                                                assignedrole__assignedrolestatus__role_status__status="Activated").values(
            assigned_role=F('assignedrole__assigned_role_id'),
            user_org_role=F('org_role_id'),
            user_role=F('role__role'),
            status=F('assignedrole__assignedrolestatus__role_status__status'),
        )
        return queryset

    @classmethod
    def get_all_user_notifications(cls, user_id):
        ids = cls.get_users_ids(user_id)
        user_notifications = []

        for user_id_entry in ids:
            user_notifications.extend(
                UserNotification.objects.filter(
                    assigned_role_id=user_id_entry['assigned_role']
                ).values(
                    id=F('request_notification__notification__notification_id'),
                    type=F('request_notification__notification__notification_type'),
                    read=F('request_notification__notification__read'),
                    authored_on=F('request_notification__notification__authored_on'),
                    message=F('request_notification__notification__message'),
                    role=F('assigned_role__org_role__role__role')
                )
            )

            user_notifications.extend(
                GroupNotification.objects.filter(
                    org_role_id=user_id_entry['user_org_role']
                ).values(
                    id=F('request_notification__notification__notification_id'),
                    type=F('request_notification__notification__notification_type'),
                    read=F('request_notification__notification__read'),
                    authored_on=F('request_notification__notification__authored_on'),
                    message=F('request_notification__notification__message'),
                    role=F('org_role__role__role')
                )
            )
        # Convert datetime objects to ISO 8601 format
        for notification in user_notifications:
            notification['authored_on'] = notification['authored_on'].isoformat()

        return user_notifications or []


def send_email_notifications(details, reviewer_message=None, requester_message=None):
    mail_sender = MailSender()

    if details.get("requester_email") is not None:
        mail_sender.send_html(subject="Request Notification",
                              message=requester_message,
                              recipient_list=[details["requester_email"]])
        logger.info(f'Sending an email to {details["requester_email"]} with message: "{requester_message}"')

    if details.get("org_emails") is not None:
        for email_address in details["org_emails"]:
            if email_address["email"]:
                mail_sender.send_html(subject="Request Notification",
                                      message=reviewer_message, recipient_list=[email_address["email"]])
                logger.info(f'Sending an email to {email_address["name"]}: {email_address["email"]} with message: "{reviewer_message}"')


class RequestNotificationCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = RequestNotification.objects.all()
    serializer_class = RequestNotificationSerializer

    # Looking for the previous States if they are approved
    @classmethod
    def check_previous_state(cls, state_id):
        queryset = NextState.objects.all().filter(next_id=state_id).select_related('current_state').values(
            status=F('current_state__state_lookup__state'),
            stage_type=F('current_state__stage_type'),
            role=F('current_state__org_role__role__role')
        )
        queryset = list(queryset)
        # is_requester checks if the previous role is a request and approved checks if the previous state is approved
        approved = all(r['status'] == APPROVED_STATUS for r in queryset)
        is_requester = all(r['role'] == DATA_REQUESTER_ROLE for r in queryset)
        return approved, is_requester

    @classmethod
    def previousStatesApproved(cls, state_id):
        queryset = NextState.objects.all().filter(next_id=state_id).select_related('current_state').values(
            'current_state__state_lookup__state'
        ).annotate(
            status=F('current_state__state_lookup__state'),
            stage_type=F('current_state__stage_type')
        )
        queryset = list(queryset)
        allApproved = True
        for q in queryset:
            if q['status'] != 'Approved':
                allApproved = False
        return allApproved

    @classmethod
    def verify_merge_previous_states(cls, state_id):
        queryset = NextState.objects.all().filter(current_state_id=state_id).select_related('next').values(
            'next_id'
        ).annotate(
            stage_type=F('next__stage_type')
        )
        queryset = list(queryset)
        all_approved = True
        for q in queryset:
            if not cls.previousStatesApproved(q['next_id']):
                all_approved = False
                break  # Exit the loop if any merge is not approved
        return all_approved

    # this function checks for the next state
    @classmethod
    def check_next_state(cls, state_id):
        queryset = NextState.objects.all().filter(current_state_id=state_id).select_related('next').values(
            role=F('next__org_role__role__role'),
            status=F('current_state__state_lookup__state'),
        )
        result = list(queryset)
        # the single checks if the next role is a request and denied checks if the next state is denied
        single = any(n['role'] == DATA_REQUESTER_ROLE for n in result)
        denied = any(r['status'] == DENIED_STATUS for r in result)
        print("Single: ", single)
        print("Denied: ", denied)
        return single, denied

    @classmethod
    def next_state_org_role(cls, state):
        queryset = NextState.objects.filter(current_state_id=state).select_related('current_state').values(
            org_role_id=F('current_state__org_role_id'),
            next_state=F('current_state_id')
        ).distinct()

        first_item = queryset.first() if queryset.exists() else None
        result = {
            'org_role_id': first_item.get('org_role_id') if first_item else None,
            'next_state': first_item.get('next_state') if first_item else None,
        }

        return result

    # a function to create custom notification messages
    @classmethod
    def custom_notification_message(cls, state):
        queryset = NextState.objects.all().filter(current_state_id=state).select_related('current_state').values(
            role=F('current_state__org_role__role__role'),
            title=F('current_state__request__title'),
        ).distinct()
        queryset = list(queryset)
        print(queryset)
        first_item = queryset[0]
        print(first_item)
        # role messages based on the role
        role_messages = {
            DATA_SECURITY_APPROVER_ROLE: "A request titled " + first_item[
                'title'] + " has been reviewed and is now awaiting your approval.",
            DATA_ACCESS_APPROVER_ROLE: "A request titled " + first_item[
                'title'] + " has been reviewed and is now awaiting your approval.",
            DATA_CUSTODIAN_ROLE: "A request titled " + first_item[
                'title'] + " has been approved by all data security and access officers and is now awaiting your endorsement.",
            DATA_OFFICER_ROLE: "A request titled " + first_item[
                'title'] + " has been endorsed by the Data Custodian and is now awaiting data extraction."
        }

        for item in queryset:
            role = item['role']
            for roles, message_template in role_messages.items():
                if role in roles:
                    return message_template + " Check on the iDARP web app for more details"
        return "Default message if no matching role is found."

    # this function gets the request details
    @classmethod
    def get_request_details(cls, state, user, group):
        org_emails = []
        if user and group:
            # This branch is executed when both user and group are truthy
            details = RequestState.objects.all().filter(request_state_id=state).select_related('request').values(
                assigned_role=F('request__requester__assigned_role_id'),
                requester_email=F('request__requester__user__org_email'),
                requester_name=F('request__requester__user__fname'),
                user_org_role=F('org_role_id'),
                state_id=F('request_state_id'),
                title=F('request__title')
            ).first()  # Retrieve the first item from the QuerySet
            org_emails.extend(
                AssignedRole.objects.filter(
                    org_role_id=details['user_org_role']
                ).values(
                    name=F('user__fname'),
                    email=F('user__org_email')
                )
            )
            # Add org_emails to the details dictionary
            details['org_emails'] = org_emails
            return details
        elif not user and group:
            # This branch is executed when user is falsy (not truthy) and group is truthy
            details = RequestState.objects.all().filter(request_state_id=state).select_related('request').values(
                user_org_role=F('org_role_id'),
                state_id=F('request_state_id'),
                title=F('request__title')
            ).first()  # Retrieve the first item from the QuerySet
            org_emails.extend(
                AssignedRole.objects.filter(
                    org_role_id=details['user_org_role']
                ).values(
                    name=F('user__fname'),
                    email=F('user__org_email')
                )
            )
            # Add org_emails to the details dictionary
            details['org_emails'] = org_emails
            return details
        elif user and not group:
            # This branch is executed when group is falsy (not truthy) and user is truthy
            details = RequestState.objects.all().filter(request_state_id=state).select_related('request').values(
                assigned_role=F('request__requester__assigned_role_id'),
                requester_email=F('request__requester__user__org_email'),
                requester_name=F('request__requester__user__fname'),
                state_id=F('request_state_id'),
                title=F('request__title')
            ).first()  # Retrieve the first item from the QuerySet
            return details

    # this function triggers different variation of notification based on different scenarios
    @classmethod
    def create_request_notification(cls, state, message=None):
        state_id = state

        approved, isRequester = cls.check_previous_state(state_id)
        is_last_state, denied = cls.check_next_state(state_id)
        next_state = cls.next_state_org_role(state_id)
        # Notify both Data Requester and Groups when approved by another role
        if approved and not isRequester and not is_last_state and not denied:
            logger.info("approved, is_not_requester, is_not_last_state, not_denied")
            details = cls.get_request_details(state_id, True, True)
            details['user_org_role'] = next_state['org_role_id']
            details['state_id'] = next_state['next_state']
            if message is not None:
                details["requester_email"] = None
                logger.info("message was passed")
                cls.notification_creation(details, message, False, True)
                send_email_notifications(details, reviewer_message=message)
            else:
                reviewer_message = cls.custom_notification_message(state_id)
                requester_message = ("One part of your Request titled " + details[
                    'title'] + ", has been approved check the progress on the iDarp website for more information")
                if cls.verify_merge_previous_states(state_id):
                    cls.notification_creation(details, reviewer_message, False, True)
                else:
                    cls.notification_creation(details, reviewer_message, False, True)
                cls.notification_creation(details, requester_message, True, False)
                send_email_notifications(details, reviewer_message, requester_message)

        # Notify Group only when submitted by Data Requester
        elif approved and isRequester and not is_last_state and not denied:
            logger.info("approved, is_requester, is_not_last_state, not_denied")
            details = cls.get_request_details(state_id, False, True)
            if message is None:
                message = "New Request titled " + details['title'] + " was submitted, awaiting your review."
            else:
                logger.info("message was passed")
            cls.notification_creation(details, message, False, True)
            send_email_notifications(details, reviewer_message=message)

        # Notify User only when approved by another role
        elif approved and not isRequester and is_last_state and not denied:
            logger.info("approved, is_not_requester, is_last_state, not_denied")
            details = cls.get_request_details(state_id, True, False)
            if message is None:
                message = ("Your request titled " + details[
                    'title'] + ", has finally been approved at all stages, check on the iDARP"
                               " website for more information")
                cls.notification_creation(details, message, True, False)
                send_email_notifications(details, requester_message=message)
            else:
                logger.info("message was passed")
                cls.notification_creation(details, message, False, True)
                send_email_notifications(details, requester_message=message)

        # Notify User only when request is denied by another role
        elif denied:
            logger.info("denied")
            details = cls.get_request_details(state_id, True, False)
            message = "Your data request titled " + details[
                'title'] + ", has been denied, Please check on the iDARP website for more information"
            cls.notification_creation(details, message, True, False)
            send_email_notifications(details, requester_message=message)

        if message:  # Notification is a reminder
            request_state = RequestState.objects.get(request_state_id=state_id)
            request_state.reminders_count += 1
            request_state.save()

    # this function creates a all related notification for each scenario
    @classmethod
    def notification_creation(cls, details, message, user, group):
        try:
            # All database operations within this block will be part of the same transactions
            with transaction.atomic():

                # Create a notification
                notification = Notification.objects.create(
                    message=message,
                    notification_type='request'
                )
                notificationid = notification.pk

                # Create a request notification
                request_notification = RequestNotification.objects.create(
                    notification_id=notificationid,
                    request_state_id=details['state_id']
                )
                requestnotificationid = request_notification.pk

                if group:
                    # Create a group notification
                    GroupNotification.objects.create(
                        request_notification_id=requestnotificationid,
                        org_role_id=details['user_org_role']
                    )

                if user:
                    # Create a user notification (if assigned role is provided)
                    UserNotification.objects.create(
                        request_notification_id=requestnotificationid,
                        assigned_role_id=details['assigned_role']
                    )

        except Exception as e:
            # Handle exceptions that may occur during the transaction
            print(f"Error creating request notification: {e}")


class PatchRequestNotificationView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    lookup_field = 'notification_id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Only updating the 'read' field
        partial_data = {'read': True}
        serializer = self.get_serializer(instance, data=partial_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @classmethod
    def update_notification_read_status(cls, state_id, org_role_id):
        queryset = GroupNotification.objects.filter(
            org_role_id=org_role_id,
            request_notification__request_state_id=state_id
        ).values(
            notification_id=F('request_notification__notification__notification_id'),
        )

        if queryset.exists():
            notification_id = queryset.first()['notification_id']

            update_notification = Notification.objects.get(pk=notification_id)
            update_notification.read = True
            update_notification.save()
