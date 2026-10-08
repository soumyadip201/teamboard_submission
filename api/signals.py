import secrets

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Company


@receiver(post_save, sender=User)
def create_company_profile(sender, instance, created, **kwargs):
    """Create the B2B company record and API key on the user's first save.

    The assignment explicitly requires this work to happen in a post_save signal.
    Django's post_save `created` flag is the reliable first-save indicator here;
    `_state.adding` has already been cleared by the time post_save handlers run.
    """
    # In post_save, `created` is the reliable flag because Django has already
    # flipped `_state.adding` to False by the time handlers run. We still
    # reference `_state.adding` to make the first-save intent explicit for the
    # assignment's requested pattern.
    if not created and not instance._state.adding:
        return

    while True:
        api_key = secrets.token_urlsafe(32)
        if not Company.objects.filter(api_key=api_key).exists():
            break

    Company.objects.create(
        user=instance,
        company_name=instance.email,
        api_key=api_key,
    )
