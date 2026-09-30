from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reviews", "0008_ruleversion_approval_audit")]

    operations = [
        migrations.AlterField(
            model_name="extractedfield",
            name="review_status",
            field=models.CharField(
                choices=[
                    ("AUTO_ACCEPTED", "Auto accepted"),
                    ("HUMAN_ACCEPTED", "Human accepted"),
                    ("NEEDS_REVIEW", "Needs review"),
                    ("REJECTED", "Rejected"),
                ],
                default="NEEDS_REVIEW",
                max_length=30,
            ),
        ),
    ]
