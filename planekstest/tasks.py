import logging

from django.contrib.auth import get_user_model

from api.mailing import send_register_email, send_new_comment
#from api.v1.post.serializers import PostCreateSerializer
from planekstest.celery import app


@app.task
def send_verification_email(user_id, token):
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(pk=user_id)
        send_register_email(user, token)
    except UserModel.DoesNotExist:
        logging.warning("Tried to send email to non-existing user '%s'" % user_id)

@app.task
def send_new_comment_email(target_email, post_link):
    send_new_comment(target_email, post_link)

