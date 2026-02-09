# Generated migration to add assigned_to field to FaultReport

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gridapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='faultreport',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='faults_assigned', to='gridapp.staff'),
        ),
        migrations.AlterField(
            model_name='faultreport',
            name='reported_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='faults_reported', to='gridapp.staff'),
        ),
    ]
