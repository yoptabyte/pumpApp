from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('pamp_app', '0005_alter_telegramlink_linking_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramlink',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='profile',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='posts', to='pamp_app.profile'),
        ),
        migrations.AddConstraint(
            model_name='postimage',
            constraint=models.CheckConstraint(
                condition=models.Q(('image__isnull', False), ('image_url__isnull', True), _connector='AND') | models.Q(('image__isnull', True), ('image_url__isnull', False), _connector='AND'),
                name='post_image_requires_exactly_one_source',
            ),
        ),
        migrations.AddConstraint(
            model_name='postvideo',
            constraint=models.CheckConstraint(
                condition=models.Q(('video__isnull', False), ('video_url__isnull', True), _connector='AND') | models.Q(('video__isnull', True), ('video_url__isnull', False), _connector='AND'),
                name='post_video_requires_exactly_one_source',
            ),
        ),
    ]
