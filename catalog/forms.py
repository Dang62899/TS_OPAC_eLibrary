from django import forms
from .models import Publication, PublicationType, Item


class PublicationForm(forms.ModelForm):
    """Form for creating and editing publications"""
    class Meta:
        model = Publication
        fields = [
            'title', 'subtitle', 'publication_type', 'authors', 'subjects',
            'publisher', 'publication_date', 'edition', 'isbn', 'language',
            'pages', 'call_number', 'abstract', 'summary', 'cover_image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Publication Title'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subtitle (optional)'}),
            'publication_type': forms.Select(attrs={'class': 'form-select'}),
            'authors': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'publisher': forms.Select(attrs={'class': 'form-select'}),
            'publication_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'edition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1st Edition'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN (optional)'}),
            'language': forms.TextInput(attrs={'class': 'form-control', 'value': 'English'}),
            'pages': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of pages'}),
            'call_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Classification number'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description'}),
            'summary': forms.Textarea(
                attrs={
                    'class': 'form-control', 'rows': 4,
                    'placeholder': 'Detailed summary (optional)'
                }
            ),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ItemForm(forms.ModelForm):
    """Form for adding items (copies) to publications"""
    class Meta:
        model = Item
        fields = ['barcode', 'location', 'status', 'condition']
        widgets = {
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barcode number'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
        }


class SearchForm(forms.Form):
    """Advanced search form for catalog"""
    SEARCH_FIELDS = [
        ('all', 'All Fields'),
        ('title', 'Title'),
        ('author', 'Author'),
        ('subject', 'Subject'),
        ('call_number', 'Call Number'),
        ('isbn', 'ISBN'),
    ]

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search...'})
    )
    search_field = forms.ChoiceField(
        choices=SEARCH_FIELDS,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    publication_type = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All Types',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    language = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Language'})
    )
    year_from = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'From Year'})
    )
    year_to = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'To Year'})
    )
    available_only = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['publication_type'].queryset = PublicationType.objects.all()
