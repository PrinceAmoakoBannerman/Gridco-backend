from django.db import models
from django.core.exceptions import ValidationError
import datetime


def validate_file_size(value):
    """Validate uploaded file is under 10MB"""
    limit = 10 * 1024 * 1024  # 10MB
    if value.size > limit:
        raise ValidationError('File too large. Maximum size is 10MB.')


def validate_file_extension(value):
    """Validate file has allowed extension"""
    import os
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx']
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported file extension. Allowed: {", ".join(valid_extensions)}')


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


class ServerRoomVisitor(models.Model):
    staff_id = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    purpose = models.TextField()
    date = models.DateField(default=datetime.date.today)
    time_in = models.TimeField()
    time_out = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.staff_id} - {self.name} - {self.date}"


class FaultReport(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField()
    date_reported = models.DateField()
    reported_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='faults_reported')
    assigned_to = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='faults_assigned')
    location = models.CharField(max_length=200)
    severity = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default='open', db_index=True)
    resolution_remarks = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to='attachments/', 
        null=True, 
        blank=True,
        validators=[validate_file_size, validate_file_extension]
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_reported']
        indexes = [
            models.Index(fields=['-date_reported']),
            models.Index(fields=['status', '-date_reported']),
        ]


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


class FaultFeedback(models.Model):
    fault = models.ForeignKey(FaultReport, on_delete=models.CASCADE, related_name='feedbacks')
    staff_name = models.CharField(max_length=200)
    staff_email = models.EmailField()
    feedback_text = models.TextField()
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback on {self.fault.title} by {self.staff_name}"

    class Meta:
        ordering = ['-date_submitted']


class AuditLog(models.Model):
    """Track all changes made to records in the system"""
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('ATTACHMENT_DELETE', 'Attachment Deleted'),
        ('BULK_DELETE', 'Bulk Delete'),
        ('BULK_UPDATE', 'Bulk Update'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)  # e.g., 'FaultReport', 'FieldActivity'
    object_id = models.IntegerField()
    user = models.CharField(max_length=200, default='system')  # Can be staff name or 'system'
    changes = models.JSONField(default=dict)  # {field: {'old': old_value, 'new': new_value}}
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.action} - {self.model_name}({self.object_id}) by {self.user}"
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]

