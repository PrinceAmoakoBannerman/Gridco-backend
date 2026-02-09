from django.db import models


class Staff(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ServerRoomEntry(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField()
    time_in = models.TimeField()
    time_out = models.TimeField(null=True, blank=True)
    reason = models.TextField()
    equipment_touched = models.TextField(blank=True)
    supervisor = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.staff} - {self.date}"


class FaultReport(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    date_reported = models.DateField()
    reported_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=200)
    severity = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default='open')
    resolution_remarks = models.TextField(blank=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)

    def __str__(self):
        return self.title


class FieldActivity(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    substation = models.CharField(max_length=200)
    date = models.DateField()
    time_out = models.TimeField()
    time_returned = models.TimeField(null=True, blank=True)
    purpose = models.TextField(blank=True)
    work_done = models.TextField(blank=True)
    materials_used = models.TextField(blank=True)
    supervisor_approval = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.staff} @ {self.substation} on {self.date}"
