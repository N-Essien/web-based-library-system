from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.index, name='/'),
    path('signup/', views.user_signup, name='user_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Book Catalog and Borrowing
    path('catalog/', views.catalog, name='catalog'), 
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'), 
    path('access_pdf/<int:book_id>/', views.access_pdf, name='access_pdf'), 
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),

    # admin urls
    path('admin/library/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/approve_request/<int:request_id>/', views.approve_request, name='approve_request'),
]