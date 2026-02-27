from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- Authentication Routes ---
    # Points to your custom login.html template
    path('login/', auth_views.LoginView.as_view(template_name='parking/login.html'), name='login'),
    
    # Redirects back to login page after logging out
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # --- Core Application Routes ---
    path('', views.dashboard, name='dashboard'),
    path('entry/', views.vehicle_entry, name='entry'),
    path('exit/', views.vehicle_exit, name='exit'),
    
    # --- Reports & PDF Routes ---
    path('reports/', views.revenue_report_page, name='revenue_reports'),
    path('report/pdf/', views.export_pdf_report, name='export_pdf'),
    path('receipt/<int:transaction_id>/', views.generate_receipt_pdf, name='generate_receipt'),
]