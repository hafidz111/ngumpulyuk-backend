from django.db.models.signals import post_save
from django.dispatch import receiver

from ngumpulyuk_app.communities.models import Community, CommunityMember


@receiver(post_save, sender=Community)
def add_community_creator_as_admin(sender, instance, created, **kwargs):
    if created:
        CommunityMember.objects.get_or_create(
            community=instance,
            user=instance.creator,
            defaults={"role": "owner"},
        )
