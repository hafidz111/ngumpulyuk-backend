import uuid

from django.conf import settings
from django.db import models
from django.db.models import F


class Community(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50)
    cover_image = models.CharField(max_length=255, blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_communities",
    )
    member_count = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "communities"
        verbose_name_plural = "communities"


class CommunityMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_memberships",
    )
    role = models.CharField(
        max_length=20,
        default="member",
        choices=[
            ("owner", "owner"),
            ("admin", "admin"),
            ("moderator", "moderator"),
            ("member", "member"),
        ],
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "community_members"
        unique_together = [["community", "user"]]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            Community.objects.filter(pk=self.community_id).update(
                member_count=F("member_count") + 1
            )

    def delete(self, *args, **kwargs):
        cid = self.community_id
        super().delete(*args, **kwargs)
        Community.objects.filter(pk=cid).update(member_count=F("member_count") - 1)
