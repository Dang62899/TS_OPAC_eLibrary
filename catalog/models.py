from django.db import models
from django.utils import timezone
from django.urls import reverse


class PublicationType(models.Model):
    """Types of publications: Manuals, SOPs, Capstone Projects, TTPs"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Subject categories for publications"""
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Author(models.Model):
    """Authors of publications"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Publisher(models.Model):
    """Publishers of publications"""
    name = models.CharField(max_length=200, unique=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Location(models.Model):
    """Physical or digital locations in the library"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_physical = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Publication(models.Model):
    """Main publication/book record"""
    title = models.CharField(max_length=500)
    subtitle = models.CharField(max_length=500, blank=True)
    authors = models.ManyToManyField(Author, related_name='publications')
    publication_type = models.ForeignKey(PublicationType, on_delete=models.PROTECT, related_name='publications')
    subjects = models.ManyToManyField(Subject, related_name='publications', blank=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='publications')
    publication_date = models.DateField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    isbn = models.CharField(max_length=20, blank=True, verbose_name='ISBN')
    # Normalized ISBN (digits only, no hyphens/spaces) for fast lookups
    normalized_isbn = models.CharField(max_length=20, blank=True, db_index=True)
    language = models.CharField(max_length=50, default='English')
    pages = models.IntegerField(null=True, blank=True)
    abstract = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    call_number = models.CharField(max_length=100, blank=True)

    # Metadata
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['call_number']),
            models.Index(fields=['normalized_isbn']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('catalog:publication_detail', args=[str(self.id)])

    def get_authors_display(self):
        """Return comma-separated list of authors"""
        return ", ".join([str(author) for author in self.authors.all()])

    def save(self, *args, **kwargs):
        # Normalize ISBN for consistent lookups: remove hyphens/spaces
        if self.isbn:
            self.normalized_isbn = self.isbn.replace('-', '').replace(' ', '')
        else:
            self.normalized_isbn = ''
        super().save(*args, **kwargs)

    def get_available_copies_count(self):
        """Return number of available copies"""
        return self.items.filter(status='available').count()

    def get_total_copies_count(self):
        """Return total number of copies"""
        return self.items.count()

    def is_available(self):
        """Check if any copy is available"""
        return self.get_available_copies_count() > 0


class Item(models.Model):
    """Physical or digital copy of a publication"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('on_loan', 'On Loan'),
        ('in_transit', 'In Transit'),
        ('on_hold_shelf', 'On Hold Shelf'),
        ('processing', 'Processing'),
        ('missing', 'Missing'),
        ('damaged', 'Damaged'),
        ('withdrawn', 'Withdrawn'),
    ]

    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='items')
    barcode = models.CharField(max_length=100, unique=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='items')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    condition = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Acquisition information
    acquisition_date = models.DateField(default=timezone.now)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Circulation statistics
    times_borrowed = models.IntegerField(default=0)
    last_borrowed_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['barcode']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.publication.title} - {self.barcode}"

    def get_status_display_with_date(self):
        """Get status with due date if on loan"""
        if self.status == 'on_loan':
            from circulation.models import Loan
            try:
                loan = Loan.objects.get(item=self, status='active')
                return f"On Loan - Due {loan.due_date.strftime('%m/%d/%Y')}"
            except Loan.DoesNotExist:
                pass
        return self.get_status_display()

    def is_available_for_loan(self):
        """Check if item can be loaned"""
        return self.status == 'available'
