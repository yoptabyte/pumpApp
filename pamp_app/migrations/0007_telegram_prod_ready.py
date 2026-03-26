from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('pamp_app', '0006_telegramlink_expires_at_and_media_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingsession',
            name='timezone',
            field=models.CharField(default='Europe/Lisbon', max_length=64),
        ),
        migrations.AddField(
            model_name='telegramlink',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='telegramlink',
            name='last_interaction_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='telegramlink',
            name='linked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='telegramlink',
            name='telegram_user_id',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True, unique=True),
        ),
        migrations.RemoveField(
            model_name='telegramlink',
            name='linking_code',
        ),
        migrations.RemoveField(
            model_name='telegramlink',
            name='expires_at',
        ),
        migrations.CreateModel(
            name='TelegramLinkToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_hash', models.CharField(max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telegram_link_tokens', to='auth.user')),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'expires_at'], name='pamp_app_te_user_id_9d18b7_idx')],
            },
        ),
        migrations.CreateModel(
            name='TrainingSessionOccurrence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('starts_at', models.DateTimeField(db_index=True)),
                ('source_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('training_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='occurrences', to='pamp_app.trainingsession')),
            ],
            options={
                'ordering': ['starts_at'],
                'constraints': [models.UniqueConstraint(fields=('training_session', 'starts_at'), name='unique_training_session_occurrence')],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('telegram', 'Telegram')], default='telegram', max_length=20)),
                ('kind', models.CharField(choices=[('training_reminder', 'Training Reminder')], default='training_reminder', max_length=50)),
                ('scheduled_for', models.DateTimeField(db_index=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], db_index=True, default='pending', max_length=20)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('occurrence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='pamp_app.trainingsessionoccurrence')),
                ('telegram_link', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='pamp_app.telegramlink')),
            ],
            options={
                'ordering': ['scheduled_for'],
                'constraints': [models.UniqueConstraint(fields=('telegram_link', 'occurrence', 'kind'), name='unique_notification_per_occurrence_kind')],
            },
        ),
    ]
