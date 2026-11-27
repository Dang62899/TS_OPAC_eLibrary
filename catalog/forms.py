from django import forms
from django.conf import settings
import os
from .models import Publication, PublicationType, Item, Location, Attachment
from .models import Author, Subject
from elibrary.choices import UNIT_CHOICES


class PublicationForm(forms.ModelForm):
    """Form for creating and editing publications"""

    class Meta:
        model = Publication
        fields = [
            "title",
            "subtitle",
            "publication_type",
            "authors",
            "subjects",
            "publisher",
            "publication_date",
            "edition",
            "isbn",
            "language",
            "pages",
            "call_number",
            "research_year",
            "research_class",
            "abstract",
            "summary",
            "cover_image",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Publication Title"}),
            "subtitle": forms.TextInput(attrs={"class": "form-control", "placeholder": "Subtitle (optional)"}),
            "publication_type": forms.Select(attrs={"class": "form-select"}),
            "authors": forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
            "subjects": forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
            "publisher": forms.Select(attrs={"class": "form-select"}),
            "publication_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "edition": forms.TextInput(attrs={"class": "form-control", "placeholder": "1st Edition"}),
            "isbn": forms.TextInput(attrs={"class": "form-control", "placeholder": "ISBN (optional)"}),
            "language": forms.TextInput(attrs={"class": "form-control", "value": "English"}),
            "pages": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Number of pages"}),
            "call_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Classification number"}),
            "research_year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Research Year (e.g., 2024)"}),
            "research_class": forms.TextInput(attrs={"class": "form-control", "placeholder": "Class/Year Group"}),
            "abstract": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Brief description"}),
            "summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Detailed summary (optional)"}
            ),
            "cover_image": forms.FileInput(attrs={"class": "form-control"}),
        }


class ItemForm(forms.ModelForm):
    """Form for adding items (copies) to publications"""

    class Meta:
        model = Item
        fields = ["barcode", "location", "status", "condition"]
        widgets = {
            "barcode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Barcode number"}),
            "location": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "condition": forms.Select(attrs={"class": "form-select"}),
        }


class SearchForm(forms.Form):
    """One all-fields catalog query with optional collection-wide filters."""

    query = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Search..."})
    )
    search_in = forms.ChoiceField(
        choices=[
            ("all", "All fields"),
            ("title", "Title"),
            ("author", "Author"),
            ("subject", "Subject"),
            ("call_number", "Call number"),
            ("isbn", "ISBN"),
            ("description", "Description"),
        ],
        required=False,
        initial="all",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    publication_types = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    authors = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    language = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Language"})
    )
    research_class = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Class or year group"})
    )
    unit = forms.ChoiceField(
        choices=[("", "Any unit"), *UNIT_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    resource_type = forms.ChoiceField(
        choices=[("", "Any resource"), *Attachment.ATTACHMENT_TYPES],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    tag = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Resource tag"})
    )
    format = forms.ChoiceField(
        choices=[("", "Any format"), ("pdf", "PDF"), ("pptx", "PowerPoint"), ("docx", "Word"), ("mp4", "Video")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    downloadable = forms.ChoiceField(
        choices=[("", "Any"), ("true", "Downloadable"), ("false", "Protected")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    year_from = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "From Year"})
    )
    year_to = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "To Year"})
    )
    available_only = forms.BooleanField(
        required=False, initial=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    location = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Locations",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    sort_by = forms.ChoiceField(
        choices=[
            ("relevance", "Relevance"),
            ("title", "Title"),
            ("date", "Newest"),
            ("date_asc", "Oldest"),
            ("popularity", "Most Borrowed"),
        ],
        required=False,
        initial="relevance",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publication_types"].queryset = PublicationType.objects.all()
        self.fields["location"].queryset = Location.objects.all()
        self.fields["authors"].queryset = Author.objects.all()
        self.fields["subjects"].queryset = Subject.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        year_from = cleaned_data.get("year_from")
        year_to = cleaned_data.get("year_to")
        if year_from and year_to and year_from > year_to:
            self.add_error("year_to", "End year must be the same as or later than start year.")
        return cleaned_data
class AttachmentForm(forms.ModelForm):
    unit = forms.ChoiceField(
        choices=[("", "Select a unit"), *UNIT_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Attachment
        fields = ["attachment_type", "file", "is_external", "external_url", "allow_download", "year", "class_field", "unit", "tags", "merge_first_two_pages", "description", "duration_seconds"]
        widgets = {
            "attachment_type": forms.Select(attrs={"class": "form-select"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_external": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "external_url": forms.URLInput(attrs={"class": "form-control"}),
            "allow_download": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "class_field": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.TextInput(attrs={"class": "form-control", "placeholder": "Comma-separated tags"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "duration_seconds": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_unit = getattr(self.instance, "unit", "")
        if current_unit and current_unit not in dict(UNIT_CHOICES):
            self.fields["unit"].choices = [("", "Select a unit"), (current_unit, current_unit), *UNIT_CHOICES]

    def clean(self):
        cleaned_data = super().clean()
        is_external = cleaned_data.get("is_external")
        uploaded_file = cleaned_data.get("file")
        external_url = cleaned_data.get("external_url")

        if is_external:
            if not external_url:
                self.add_error("external_url", "Enter a URL for an external resource.")
            if uploaded_file:
                self.add_error("file", "Remove the uploaded file when using an external URL.")
        elif not uploaded_file:
            self.add_error("file", "Choose a file or select the external URL option.")
        else:
            allowed_extensions = {".pdf", ".pptx", ".docx", ".mp4"}
            extension = os.path.splitext(uploaded_file.name)[1].lower()
            if extension not in allowed_extensions:
                self.add_error("file", "Choose a PDF, PPTX, DOCX, or MP4 file that supports watermarking.")

            max_size = int(getattr(settings, "MAX_ATTACHMENT_SIZE_MB", 50)) * 1024 * 1024
            if uploaded_file.size > max_size:
                self.add_error("file", f"The file must be no larger than {max_size // (1024 * 1024)} MB.")

        return cleaned_data

    def save(self, commit=True):
        attachment = super().save(commit=False)
        if commit:
            attachment.save()
            self.save_m2m()
        return attachment


class AttachmentDownloadPasswordForm(forms.Form):
    password = forms.CharField(
        strip=False,
        label="Download password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-sm", "autocomplete": "current-password"}
        ),
    )

