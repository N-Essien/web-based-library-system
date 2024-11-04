from datetime import timedelta
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from library.forms import LoginForm, UserSignupForm
from library.models import Book, BorrowRequest, User


def index(request):
    return redirect('/catalog/')

# Create your views here.
def user_signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('catalog')
        print(form.error_messages)
    else:
        form = UserSignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_admin:
                    return redirect('admin_dashboard')
                else:
                    return redirect('catalog')
            else:
                messages.error(request, 'credentials not found')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

@login_required(login_url='/login/')
def catalog(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        books = Book.objects.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query)
        )
    else:
        books = Book.objects.all()
        
    context = {
        'books': books,
    }
    return render(request, 'catalog.html', context)

@login_required(login_url='/login/')
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if book.is_available:
        # Create a borrow request (pending admin approval)
        borrow_request = BorrowRequest.objects.create(user=request.user, book=book)
        messages.success(request, f'Borrow request for "{book.title}" submitted. Please wait for admin approval.')
    else:
        messages.error(request, f'The book "{book.title}" is not available right now. Please check back later.')
    
    return redirect('catalog')


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('catalog')
    
    borrow_requests = BorrowRequest.objects.filter(approved=False)
    users = User.objects.filter(is_admin=False)

    # Fetching borrowed books that are approved
    borrowed_books = BorrowRequest.objects.filter(approved=True)
    for borrow_request in borrowed_books:
        borrow_request.time_remaining = (borrow_request.return_time - timezone.now()).total_seconds() // 60  # Calculate time remaining in minutes

    
    return render(request, 'admin_dashboard.html', {
        'borrow_requests': borrow_requests,
        'users': users,
        'borrowed_books': borrowed_books,
    })

@login_required
def approve_request(request, request_id):
    borrow_request = BorrowRequest.objects.get(id=request_id)
    if request.user.is_superuser:
        if borrow_request.book.is_available:
            borrow_request.approved = True
            borrow_request.return_time = timezone.now() + timedelta(hours=1)
            borrow_request.save()
            messages.success(request, f'Borrow request for "{borrow_request.book.title}" approved. The user can access the book for 1 hour.')
        else:
            messages.error(request, f'The book "{borrow_request.book.title}" is not available.')
    return redirect('admin_dashboard')


@login_required
def access_pdf(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    borrow_request = BorrowRequest.objects.filter(user=request.user, book=book, approved=True).last()

    if borrow_request and borrow_request.is_accessible():
        messages.success(request, f'You can access "{book.title}" for {int((borrow_request.return_time - timezone.now()).seconds / 60)} more minutes.')
        # Return the PDF file for download
        response = HttpResponse(book.pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{book.title}.pdf"'
        return response
    else:
        messages.error(request, 'Your access to this book has expired or you do not have access.')
        return HttpResponseForbidden("You no longer have access to this book.")


@login_required
def user_dashboard(request):
    # Get current time
    now = timezone.now()
    
    # Fetch borrowed books within the last hour
    borrowed_books = BorrowRequest.objects.filter(
        user=request.user,
        approved=True,
        return_time__gt=now  # Only get requests that are still within the return time
    )

    for borrow_request in borrowed_books:
        borrow_request.time_remaining = (borrow_request.return_time - timezone.now()).total_seconds() // 60
    
    return render(request, 'user_dashboard.html', {
        'borrowed_books': borrowed_books,
    })