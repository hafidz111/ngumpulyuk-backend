import uuid

from django.conf import settings
from django.db import models
from django.db.models import F

from ngumpulyuk_app.communities.models import Community
from ngumpulyuk_app.events.models import Event


class Thread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="threads", blank=True, null=True
    )
    related_event = models.ForeignKey(
        Event, on_delete=models.SET_NULL, related_name="threads", blank=True, null=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="threads",
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    images = models.JSONField(blank=True, null=True)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "threads"


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField()
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comments"

    def save(self, *args, **kwargs):
        from ngumpulyuk_app.users.models import ActivityHistory

        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            Thread.objects.filter(pk=self.thread_id).update(comment_count=F("comment_count") + 1)
            ActivityHistory.objects.create(
                user_id=self.author_id,
                activity_type="commented",
                description="Posted a comment",
                related_type="thread",
                related_id=self.thread_id,
            )

    def delete(self, *args, **kwargs):
        tid = self.thread_id
        super().delete(*args, **kwargs)
        Thread.objects.filter(pk=tid).update(comment_count=F("comment_count") - 1)


class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes")
    likeable_type = models.CharField(
        max_length=20,
        choices=[("thread", "thread"), ("comment", "comment")],
    )
    likeable_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "likes"
        unique_together = [["user", "likeable_type", "likeable_id"]]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            if self.likeable_type == "thread":
                Thread.objects.filter(pk=self.likeable_id).update(like_count=F("like_count") + 1)
            elif self.likeable_type == "comment":
                Comment.objects.filter(pk=self.likeable_id).update(like_count=F("like_count") + 1)

    def delete(self, *args, **kwargs):
        ltype, lid = self.likeable_type, self.likeable_id
        super().delete(*args, **kwargs)
        if ltype == "thread":
            Thread.objects.filter(pk=lid).update(like_count=F("like_count") - 1)
        elif ltype == "comment":
            Comment.objects.filter(pk=lid).update(like_count=F("like_count") - 1)
