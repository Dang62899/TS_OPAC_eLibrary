from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class PublicationType(models.Model):
    """Types of publications: Manuals, SOPs, Capstone Projects, TTPs"""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Subject categories for publications"""

    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Author(models.Model):
    """Authors of publications"""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Publisher(models.Model):
    """Publishers of publications"""

    name = models.CharField(max_length=200, unique=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Location(models.Model):
    """Physical or digital locations in the library"""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_physical = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Publication(models.Model):
    """Main publication/book record"""

    title = models.CharField(max_length=500)
    subtitle = models.CharField(max_length=500, blank=True)
    authors = models.ManyToManyField(Author, related_name="publications")
    publication_type = models.ForeignKey(PublicationType, on_delete=models.PROTECT, related_name="publications")
    subjects = models.ManyToManyField(Subject, related_name="publications", blank=True)
    publisher = models.ForeignKey(
        Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name="publications"
    )
    publication_date = models.DateField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    isbn = models.CharField(max_length=20, blank=True, verbose_name="ISBN")
    # Normalized ISBN (digits only, no hyphens/spaces) for fast lookups
    normalized_isbn = models.CharField(max_length=20, blank=True, db_index=True)
    language = models.CharField(max_length=50, default="English")
    pages = models.IntegerField(null=True, blank=True)
    abstract = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="covers/", blank=True, null=True)
    call_number = models.CharField(max_length=100, blank=True)

    # Metadata
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["call_number"]),
            models.Index(fields=["normalized_isbn"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("catalog:publication_detail", args=[str(self.id)])

    def get_authors_display(self):
        """Return comma-separated list of authors"""
        return ", ".join([str(author) for author in self.authors.all()])

    def save(self, *args, **kwargs):
        # Normalize ISBN for consistent lookups: remove hyphens/spaces
        if self.isbn:
            self.normalized_isbn = self.isbn.replace("-", "").replace(" ", "")
        else:
            self.normalized_isbn = ""
        super().save(*args, **kwargs)

    def get_available_copies_count(self):
        """Return number of available copies"""
        return self.items.filter(status="available").count()

    def get_total_copies_count(self):
        """Return total number of copies"""
        return self.items.count()

    def is_available(self):
        """Check if any copy is available"""
        return self.get_available_copies_count() > 0

    def get_average_rating(self):
        """Get average rating for this publication"""
        from django.db.models import Avg
        result = self.ratings.aggregate(avg=Avg('rating'))
        return round(result['avg'] or 0, 1)

    def get_rating_count(self):
        """Get total number of ratings for this publication"""
        return self.ratings.count()

    def get_review_count(self):
        """Get total number of reviews for this publication"""
        return self.reviews.count()


class Item(models.Model):
    """Physical or digital copy of a publication"""

    STATUS_CHOICES = [
        ("available", "Available"),
        ("on_loan", "On Loan"),
        ("in_transit", "In Transit"),
        ("on_hold_shelf", "On Hold Shelf"),
        ("processing", "Processing"),
        ("missing", "Missing"),
        ("damaged", "Damaged"),
        ("withdrawn", "Withdrawn"),
    ]

    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="items")
    barcode = models.CharField(max_length=100, unique=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="items")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    condition = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Acquisition information
    acquisition_date = models.DateField(default=timezone.now)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Circulation statistics
    times_borrowed = models.IntegerField(default=0)
    last_borrowed_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["barcode"]
        indexes = [
            models.Index(fields=["barcode"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.publication.title} - {self.barcode}"

    def get_status_display_with_date(self):
        """Get status with due date if on loan"""
        if self.status == "on_loan":
            from circulation.models import Loan

            try:
                loan = Loan.objects.get(item=self, status="active")
                return f"On Loan - Due {loan.due_date.strftime('%m/%d/%Y')}"
            except Loan.DoesNotExist:
                pass
        return self.get_status_display()

    def is_available_for_loan(self):
        """Check if item can be loaned"""
        return self.status == "available"


class Rating(models.Model):
    """User ratings for publications (1-5 stars)"""

    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="publication_ratings")
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('publication', 'user')
        ordering = ['-date_added']
        indexes = [
            models.Index(fields=['publication', 'user']),
            models.Index(fields=['publication']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.publication.title}: {self.rating} stars"

    @staticmethod
    def get_average_rating(publication):
        """Get average rating for a publication"""
        from django.db.models import Avg
        result = Rating.objects.filter(publication=publication).aggregate(avg=Avg('rating'))
        return result['avg'] or 0

    @staticmethod
    def get_rating_count(publication):
        """Get total number of ratings for a publication"""
        return Rating.objects.filter(publication=publication).count()


class Review(models.Model):
    """User reviews for publications"""

    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="publication_reviews")
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    helpful_count = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False, help_text="Verified if user has borrowed this item")

    class Meta:
        ordering = ['-date_added']
        indexes = [
            models.Index(fields=['publication']),
            models.Index(fields=['user']),
            models.Index(fields=['-helpful_count']),
        ]

    def __str__(self):
        return f"Review by {self.user.username} on {self.publication.title}"

    @staticmethod
    def get_verified_reviews(publication):
        """Get verified reviews (from users who have borrowed the item)"""
        return Review.objects.filter(publication=publication, is_verified=True).order_by('-helpful_count', '-date_added')

    @staticmethod
    def get_recent_reviews(publication, limit=5):
        """Get recent reviews for a publication"""
        return Review.objects.filter(publication=publication).order_by('-date_added')[:limit]


class Wishlist(models.Model):
    """User's reading wishlist"""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="publication_wishlist")
    publications = models.ManyToManyField(Publication, related_name="wishlisted_by")
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.user.username}'s Wishlist"

    def add_publication(self, publication):
        """Add a publication to wishlist"""
        self.publications.add(publication)

    def remove_publication(self, publication):
        """Remove a publication from wishlist"""
        self.publications.remove(publication)

    def is_in_wishlist(self, publication):
        """Check if publication is in wishlist"""
        return self.publications.filter(id=publication.id).exists()


class ReadingProgress(models.Model):
    """Track user's reading progress for publications"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reading_progress")
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="reading_progress")
    
    PROGRESS_STATUS = [
        ('not_started', 'Not Started'),
        ('reading', 'Currently Reading'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    status = models.CharField(max_length=20, choices=PROGRESS_STATUS, default='not_started')
    pages_read = models.IntegerField(default=0)
    total_pages = models.IntegerField(default=0)
    percentage_complete = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'publication')
        ordering = ['-date_updated']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.publication.title}: {self.percentage_complete}%"

    def update_progress(self, pages_read, total_pages):
        """Update reading progress"""
        self.pages_read = pages_read
        self.total_pages = total_pages
        if total_pages > 0:
            self.percentage_complete = int((pages_read / total_pages) * 100)
        if self.percentage_complete >= 100 and self.status != 'completed':
            self.status = 'completed'
            self.completion_date = timezone.now().date()
        self.save()

    def get_progress_percentage(self):
        """Get reading progress as percentage"""
        return self.percentage_complete
