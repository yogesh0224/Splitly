# billsplit/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Group(models.Model):
    title = models.CharField(max_length=200)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    split_type = models.CharField(
        max_length=20,
        choices=[('one-time', 'One-time Event'), ('ongoing', 'Ongoing Flatmates')],
        default='one-time'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.split_type})"

    class Meta:
        ordering = ['-created_at']


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    accepted = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.group.title}"


class Expense(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='added_expenses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ManyToManyField(User, related_name='approved_expenses', blank=True)
    flagged_by = models.ManyToManyField(User, related_name='flagged_expenses', blank=True)
    flag_remark = models.TextField(blank=True)

    def __str__(self):
        return f"रू {self.amount} - {self.name}"


class RecurringExpense(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='recurrings')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    next_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.frequency})"


class Invite(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invites')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invites')
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('group', 'to_user')

    def __str__(self):
        return f"Invite to {self.to_user.username} for {self.group.title}"


class TimelineEntry(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='timeline')
    action = models.CharField(max_length=500)
    by_user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.by_user.username}"