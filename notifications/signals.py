import channels.layers
from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from main.utils.mail_sender import MailSender
from notifications.models import *
from data_requests.models import *

mail_sender = MailSender()


@receiver(post_save, sender=Notification)
def handle_notification_creation(sender, instance, created, **kwargs):
    # This function will be called after an instance of Notification is saved.
    # 'created' indicates whether the instance was just created or updated.
    if created:
        group_name = "fixed_group"
        message = {
            "type": "notification.created",
            "notification_id": instance.notification_id,
        }
        channel_layer = channels.layers.get_channel_layer()
        async_to_sync(channel_layer.group_send)(group_name, message)
        print('A new notification was created:', instance.notification_id, instance.message, instance.notification_type)


@receiver(post_save, sender=StateComment)
def handle_state_comment_creation(sender, instance, created, **kwargs):
    if created:
        try:
            request_state = RequestState.objects.get(request_state_id=instance.request_state_id)
            request_title = request_state.request.title
            user_email = request_state.request.requester.user.org_email
            assigned_role = AssignedRole.objects.get(assigned_role_id=instance.author_id)
            user_role = assigned_role.org_role.role.role

            if not instance.action_required:
                message = (f'A comment was added to the request titled <strong>{request_title}</strong>, in the section'
                           f' titled <strong>{instance.section}</strong>, containing the following comment: '
                           f'"{instance.comment}" by a <strong>{user_role}<strong>')
            else:
                message = (f'A comment was added to the request titled <strong>{request_title}</strong>, in the section'
                           f' titled <strong>{instance.section}</strong>, containing the following comment: '
                           f'"{instance.comment}" by a <strong>{user_role}</strong> and requires you action.')

            mail_sender.send_html(subject="Request Comment Notification",
                                  message=message,
                                  recipient_list=[user_email])
        except ObjectDoesNotExist:
            logging.error(f"Failed to retrieve related objects for state comment: {instance.id}")


@receiver(post_save, sender=Reply)
def handle_reply_creation(sender, instance, created, **kwargs):
    if created:
        print('A new reply was created: with reply', instance.reply, instance.comment_id)
        state_comment = StateComment.objects.get(comment_id=instance.comment_id)
        reply_assigned_role = AssignedRole.objects.get(assigned_role_id=instance.author_id)
        comment_assigned_role = AssignedRole.objects.get(assigned_role_id=state_comment.author.assigned_role_id)
        user_role = reply_assigned_role.org_role.role.role
        if user_role != "Data Requester":
            print("The author role is :", reply_assigned_role.org_role.role.role)

        else:
            print("The author role is :", reply_assigned_role.org_role.role.role)

# @receiver(pre_save, sender=RequestState)
# def update_notification_on_request_state_change(sender, instance, **kwargs):
#     # Check if the state_lookup has changed
#     if instance.pk:
#         try:
#             old_instance = RequestState.objects.get(pk=instance.pk)
#         except RequestState.DoesNotExist:
#             # Handle the case where there is no existing RequestState
#             return
#
#         if old_instance.state_lookup != instance.state_lookup:
#             # Check if the new state_lookup is 'Approved' or 'Denied'
#             if instance.state_lookup.state in ['Approved', 'Denied']:
#                 # Find the associated RequestNotification
#                 try:
#                     request_notification = RequestNotification.objects.get(request_state=instance)
#                 except RequestNotification.DoesNotExist:
#                     # Handle the case where there is no associated RequestNotification
#                     return
#
#                 # Update the associated Notification's read status
#                 request_notification.notification.read = True
#                 request_notification.notification.save()
