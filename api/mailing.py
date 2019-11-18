from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import get_template
from django.core.mail import send_mail
from planekstest import settings


def _send_email(
        subject, template, targets, sender=None, context=None,
):
    """
    Sends email to targets
    :param subject: The topic of email
    :param template: template name (lookup in 'templaces/emails/%s/.txt|.html')
    :param targets: one address or list of receivers
    :param sender: The sender, or settings.DEFAULT_FROM_EMAIL if None
    :param context: context for template
    :return:
    """
    if context is None:
        context = {}
    if sender is None:
        sender = settings.DEFAULT_FROM_EMAIL

    text_tmp = get_template('emails/' + template + '.txt')

    if isinstance(targets, str):
        targets = [targets]

    text_content = text_tmp.render(context)

    msg = EmailMultiAlternatives(subject, text_content, sender, targets)
    msg.send()


def send_new_comment(target_email, post_link):
    _send_email(
        'You have new comment',
        'new_comment',
        target_email,
        context={
            'post_link': post_link,

        }
    )


def send_register_email(user, token):
    _send_email(
        'Your registration on test_task', 'register_email', user.email,
        context={
            'user_email': user.email,
            'first_name': user.first_name,
            'token':  token,  # not implemented: token.get_url(request)
        },
    )
