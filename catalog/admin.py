from django.contrib import admin
from .models import (
    PublicationType,
    Subject,
    Author,
    Publisher,
    Location,
    Publication,
    Item,
    Rating,
    Review,
    Wishlist,
    ReadingProgress,
)


@admin.register(PublicationType)
class PublicationTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "description"]
    search_fields = ["name", "code"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name"]
    search_fields = ["first_name", "last_name"]


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ["name", "website"]
    search_fields = ["name"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_physical"]
    list_filter = ["is_physical"]
    search_fields = ["name", "code"]


class ItemInline(admin.TabularInline):
    model = Item
    extra = 1
    fields = ["barcode", "location", "status", "condition"]


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ["title", "publication_type", "publication_date", "isbn", "get_total_copies_count"]
    list_filter = ["publication_type", "language", "publication_date"]
    search_fields = ["title", "subtitle", "isbn", "call_number"]
    filter_horizontal = ["authors", "subjects"]
    inlines = [ItemInline]

    fieldsets = (
        ("Basic Information", {"fields": ("title", "subtitle", "authors", "publication_type")}),
        ("Publication Details", {"fields": ("publisher", "publication_date", "edition", "isbn", "language", "pages")}),
        ("Classification", {"fields": ("subjects", "call_number")}),
        ("Description", {"fields": ("abstract", "summary", "cover_image")}),
    )


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["barcode", "publication", "location", "status", "times_borrowed"]
    list_filter = ["status", "location"]
    search_fields = ["barcode", "publication__title"]
    readonly_fields = ["times_borrowed", "last_borrowed_date"]


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["user", "publication", "rating", "date_added"]
    list_filter = ["rating", "date_added"]
    search_fields = ["user__username", "publication__title"]
    readonly_fields = ["date_added", "date_updated"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "publication", "title", "rating", "helpful_count", "is_verified"]
    list_filter = ["rating", "is_verified", "date_added"]
    search_fields = ["user__username", "publication__title", "title", "content"]
    readonly_fields = ["date_added", "date_updated"]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "get_publication_count", "date_created"]
    search_fields = ["user__username"]
    filter_horizontal = ["publications"]
    readonly_fields = ["date_created"]

    def get_publication_count(self, obj):
        return obj.publications.count()
    get_publication_count.short_description = "Publications"


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "publication", "status", "percentage_complete", "date_updated"]
    list_filter = ["status", "date_updated"]
    search_fields = ["user__username", "publication__title"]
    readonly_fields = ["date_added", "date_updated", "percentage_complete"]

