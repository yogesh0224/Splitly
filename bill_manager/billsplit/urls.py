from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(
        template_name='billsplit/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-group/', views.create_group, name='create_group'),
    path('delete-group/<int:group_id>/', views.delete_group, name='delete_group'),
    path('export/', views.export_data, name='export_data'),
    
    # NEW: Split Detail
    path('split/<int:group_id>/', views.split_detail, name='split_detail'),
]