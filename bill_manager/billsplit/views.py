from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from decimal import Decimal
import json
from .models import Group, GroupMember, Expense, TimelineEntry

def home(request):
    return render(request, 'billsplit/home.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Welcome to Splitly 🎉")
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'billsplit/signup.html', {'form': form})

@login_required
def dashboard(request):
    my_groups = Group.objects.filter(
        members__user=request.user,
        members__accepted=True
    ).order_by('-created_at')

    # Pre-compute member count (safe)
    for group in my_groups:
        group.accepted_members_count = group.members.filter(accepted=True).count()

    total_groups = my_groups.count()
    total_spending = my_groups.aggregate(Sum('total'))['total__sum'] or 0
    total_members = GroupMember.objects.filter(group__in=my_groups, accepted=True).count()

    return render(request, 'billsplit/dashboard.html', {
        'groups': my_groups,
        'total_groups': total_groups,
        'total_spending': total_spending,
        'total_members': total_members,
    })


@login_required
def create_group(request):
    if request.method == 'POST':
        title = request.POST.get('title', 'New Group')
        total = Decimal(request.POST.get('total', '0'))
        split_type = request.POST.get('split_type', 'one-time')

        group = Group.objects.create(
            title=title,
            total=total,
            creator=request.user,
            split_type=split_type
        )
        GroupMember.objects.create(group=group, user=request.user, accepted=True)

        TimelineEntry.objects.create(
            group=group,
            action=f"Group created as {split_type}",
            by_user=request.user
        )

        return redirect('dashboard')
    
    return render(request, 'billsplit/create_group_form.html')

@login_required
def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id, creator=request.user)
    group.delete()
    messages.success(request, "Group deleted")
    return redirect('dashboard')

@login_required
def export_data(request):
    groups = Group.objects.filter(members__user=request.user, members__accepted=True)
    data = []
    for g in groups:
        data.append({
            'title': g.title,
            'total': str(g.total),
            'split_type': g.split_type,
            'created_at': g.created_at.isoformat(),
        })
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="splitly-data.json"'
    return response

@login_required
def split_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    # Only members can view
    if not group.members.filter(user=request.user, accepted=True).exists():
        return redirect('dashboard')

    expenses = group.expenses.all().order_by('-date')
    timeline = group.timeline.all()

    # Calculate balances for Summary tab
    accepted_members = group.members.filter(accepted=True)
    balances = {}
    contributions = {}
    total_expenses = expenses.count()
    
    for member in accepted_members:
        user = member.user
        balances[user.username] = Decimal('0.00')
        contributions[user.username] = Decimal('0.00')

    for exp in expenses:
        share = exp.amount / accepted_members.count()
        for m in accepted_members:
            balances[m.user.username] -= share
        balances[exp.added_by.username] += exp.amount
        contributions[exp.added_by.username] += exp.amount

    context = {
        'group': group,
        'expenses': expenses,
        'timeline': timeline,
        'balances': balances,
        'contributions': contributions,
        'accepted_members': accepted_members,
        'total_expenses': total_expenses,
    }
    return render(request, 'billsplit/split_detail.html', context)

@login_required
def add_expense(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        name = request.POST['name']
        amount = Decimal(request.POST['amount'])
        date = request.POST.get('date', timezone.now().date())
        
        expense = Expense.objects.create(
            group=group,
            name=name,
            amount=amount,
            date=date,
            added_by=request.user
        )
        TimelineEntry.objects.create(
            group=group,
            action=f'Expense "{name}" added',
            by_user=request.user
        )
        return redirect('split_detail', group_id=group_id)
    return render(request, 'billsplit/partials/add_expense_modal.html', {'group': group})

@login_required
def approve_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.user != expense.added_by:
        expense.approved_by.add(request.user)
        if expense.approved_by.count() >= expense.group.members.filter(accepted=True).count() - 1:
            expense.status = 'approved'
        expense.save()
        TimelineEntry.objects.create(
            group=expense.group,
            action=f'Expense "{expense.name}" approved',
            by_user=request.user
        )
    return redirect('split_detail', group_id=expense.group.id)

@login_required
def flag_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        remark = request.POST['remark']
        expense.flagged_by.add(request.user)
        expense.flag_remark = remark
        expense.save()
        TimelineEntry.objects.create(
            group=expense.group,
            action=f'Expense "{expense.name}" flagged: {remark}',
            by_user=request.user
        )
    return redirect('split_detail', group_id=expense.group.id)

@login_required
def send_invite(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    username = request.POST.get('username')
    try:
        user_to_invite = User.objects.get(username=username)
        Invite.objects.create(
            group=group,
            from_user=request.user,
            to_user=user_to_invite
        )
        TimelineEntry.objects.create(
            group=group,
            action=f'Invite sent to {username}',
            by_user=request.user
        )
        messages.success(request, f"Invite sent to {username}")
    except User.DoesNotExist:
        messages.error(request, "User not found")
    return redirect('split_detail', group_id=group_id)