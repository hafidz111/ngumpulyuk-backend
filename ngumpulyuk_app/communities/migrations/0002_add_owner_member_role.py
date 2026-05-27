from django.db import migrations, models


def promote_creators_to_owner(apps, schema_editor):
    Community = apps.get_model("communities", "Community")
    CommunityMember = apps.get_model("communities", "CommunityMember")
    for community in Community.objects.all().only("id", "creator_id"):
        CommunityMember.objects.filter(
            community_id=community.id,
            user_id=community.creator_id,
        ).update(role="owner")


class Migration(migrations.Migration):

    dependencies = [
        ("communities", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="communitymember",
            name="role",
            field=models.CharField(
                choices=[
                    ("owner", "owner"),
                    ("admin", "admin"),
                    ("moderator", "moderator"),
                    ("member", "member"),
                ],
                default="member",
                max_length=20,
            ),
        ),
        migrations.RunPython(promote_creators_to_owner, migrations.RunPython.noop),
    ]
