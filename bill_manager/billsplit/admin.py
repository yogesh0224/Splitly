# billsplit/admin.py
from django.contrib import admin
from .models import (
    Group, GroupMember, Expense, RecurringExpense,
    Invite, TimelineEntry
)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'split_type', 'total', 'created_at')
    list_filter = ('split_type', 'created_at')
    search_fields = ('title', 'creator__username')

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'accepted', 'joined_at')
    list_filter = ('accepted',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'group', 'added_by', 'status', 'date')
    list_filter = ('status', 'date')

@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'group', 'frequency', 'next_date')

@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ('group', 'from_user', 'to_user', 'accepted', 'created_at')

@admin.register(TimelineEntry)
class TimelineEntryAdmin(admin.ModelAdmin):
    list_display = ('action', 'by_user', 'group', 'timestamp')