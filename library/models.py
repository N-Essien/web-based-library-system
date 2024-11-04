from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

# User model for both users and admins
class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone_number']

# Book model for storing catalog
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to='books/pdfs/')  # Upload PDF files
    thumbnail = models.ImageField(upload_to='books/thumbnails/')  # Upload thumbnail images

    @property
    def is_available(self):
        """
        Checks if the most recent borrow request for the book has passed its return time.
        """
        recent_request = BorrowRequest.objects.filter(book=self, approved=True).order_by('-borrow_time').first()
        if recent_request and recent_request.return_time and recent_request.return_time > timezone.now():
            return False  # Book is still borrowed and within borrow time
        return True  # Book is available

    def __str__(self):
        return self.title

# Borrow request model for tracking borrow requests
class BorrowRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    borrow_time = models.DateTimeField(auto_now_add=True)
    return_time = models.DateTimeField(null=True, blank=True)

    def is_accessible(self):
        """
        Check if the book can still be accessed by the user (within one hour).
        """
        if self.approved and timezone.now() <= self.return_time:
            return True
        return False

    def __str__(self):
        return f"{self.user.name} - {self.book.title}"
