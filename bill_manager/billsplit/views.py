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

    # Stats
    total_groups = my_groups.count()
    total_spending = my_groups.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
    total_members = GroupMember.objects.filter(
        group__in=my_groups, accepted=True
    ).count()

    context = {
        'groups': my_groups,
        'total_groups': total_groups,
        'total_spending': total_spending,
        'total_members': total_members,
    }
    return render(request, 'billsplit/dashboard.html', context)

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

        messages.success(request, "Group created successfully!")
        return redirect('dashboard')
    return render(request, 'billsplit/partials/create_modal.html')

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