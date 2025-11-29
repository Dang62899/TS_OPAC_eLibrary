from django import forms
from django.db import models as django_models
from .models import Loan, Hold, InTransit
from catalog.models import Item, Publication
from django.db.models import F, Value
from django.db.models.functions import Replace
from accounts.models import User


class CheckoutForm(forms.ModelForm):
    """Form for checking out items"""
    # Field accepts ISBN (preferred) or item barcode as fallback
    barcode = forms.CharField(
        max_length=100,
        label='ISBN or Item ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ISBN or Item ID'
        })
    )
    borrower_card = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Library card number or username'})
    )

    class Meta:
        model = Loan
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_barcode(self):
        identifier = self.cleaned_data['barcode'].strip()
        # Try ISBN first
        if identifier:
            # Normalize input (remove hyphens/spaces)
            normalized = identifier.replace('-', '').replace(' ', '')
            # Try exact match first
            publication = Publication.objects.filter(isbn=identifier).first()
            if not publication:
                # Try normalized field lookup
                publication = Publication.objects.filter(normalized_isbn=normalized).first()
            if publication:
                # pick first available item for this publication
                item = Item.objects.filter(publication=publication, status__in=['available', 'on_hold_shelf']).first()
                if not item:
                    raise forms.ValidationError("No available items found for this ISBN.")
                self.cleaned_data['item'] = item
                return identifier
            # If we didn't find a publication by ISBN, fallback to barcode lookup
            if not publication:
                # fallback: try to find by barcode
                try:
                    item = Item.objects.get(barcode=identifier)
                    if not item.is_available_for_loan():
                        raise forms.ValidationError(f"Item is not available. Current status: {item.get_status_display()}")
                    self.cleaned_data['item'] = item
                    return identifier
                except Item.DoesNotExist:
                    raise forms.ValidationError("No publication or item found for this ISBN/ID.")
        raise forms.ValidationError("Please enter an ISBN or Item ID.")

    def clean_borrower_card(self):
        card = self.cleaned_data['borrower_card']
        try:
            borrower = User.objects.get(
                django_models.Q(library_card_number=card) | django_models.Q(username=card)
            )
            if not borrower.can_borrow():
                if borrower.is_blocked:
                    raise forms.ValidationError(f"Borrower is blocked: {borrower.block_reason}")
                else:
                    raise forms.ValidationError(f"Borrower has reached maximum loan limit ({borrower.max_items_allowed})")
            self.cleaned_data['borrower'] = borrower
            return card
        except User.DoesNotExist:
            raise forms.ValidationError("Borrower not found.")


class CheckinForm(forms.Form):
    """Form for checking in items"""
    # Field accepts ISBN (preferred) or item barcode as fallback
    barcode = forms.CharField(
        max_length=100,
        label='ISBN or Item ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ISBN or Item ID'
        })
    )

    def clean_barcode(self):
        identifier = self.cleaned_data['barcode'].strip()
        if identifier:
            # Try ISBN: find an active loan for the publication (normalize input)
            normalized = identifier.replace('-', '').replace(' ', '')
            publication = Publication.objects.filter(isbn=identifier).first()
            if not publication:
                publication = Publication.objects.filter(normalized_isbn=normalized).first()

            if publication:
                loan = Loan.objects.filter(item__publication=publication, status='active').first()
                if loan:
                    self.cleaned_data['loan'] = loan
                    return identifier
                else:
                    raise forms.ValidationError("No active loan found for this ISBN (publication).")
            else:
                # Fallback: barcode -> find item then loan
                try:
                    item = Item.objects.get(barcode=identifier)
                    loan = Loan.objects.get(item=item, status='active')
                    self.cleaned_data['loan'] = loan
                    return identifier
                except Item.DoesNotExist:
                    raise forms.ValidationError("Item not found with this ISBN/ID.")
                except Loan.DoesNotExist:
                    raise forms.ValidationError("No active loan found for this item.")
        raise forms.ValidationError("Please enter an ISBN or Item ID.")


class RenewalForm(forms.Form):
    """Form for renewing loans"""
    loan_id = forms.IntegerField(widget=forms.HiddenInput())


class HoldForm(forms.ModelForm):
    """Form for placing holds"""
    class Meta:
        model = Hold
        fields = ['pickup_location']
        widgets = {
            'pickup_location': forms.Select(attrs={'class': 'form-control'}),
        }


class InTransitForm(forms.ModelForm):
    """Form for sending items in transit"""
    barcode = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ISBN or Item ID'})
    )

    class Meta:
        model = InTransit
        fields = ['to_location', 'notes']
        widgets = {
            'to_location': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_barcode(self):
        identifier = self.cleaned_data['barcode'].strip()
        if not identifier:
            raise forms.ValidationError("Please enter an ISBN or Item ID.")

        # Try ISBN first: find a suitable item to send in transit
        normalized = identifier.replace('-', '').replace(' ', '')
        publication = None
        try:
            publication = Publication.objects.get(isbn=identifier)
        except Publication.DoesNotExist:
            publication = Publication.objects.annotate(
                _norm=Replace(Replace(F('isbn'), Value('-'), Value('')), Value(' '), Value(''))
            ).filter(_norm=normalized).first()

        if publication:
            item = Item.objects.filter(publication=publication, status__in=['available', 'on_hold_shelf']).first()
            if item:
                self.cleaned_data['item'] = item
                return identifier
            else:
                raise forms.ValidationError("No suitable item found for this ISBN to send in transit.")
        else:
            # Fallback to barcode
            try:
                item = Item.objects.get(barcode=identifier)
                self.cleaned_data['item'] = item
                return identifier
            except Item.DoesNotExist:
                raise forms.ValidationError("Item not found with this ISBN/ID.")


class BorrowerSearchForm(forms.Form):
    """Form for searching borrowers"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name, username, or card number'})
    )
    is_blocked = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('yes', 'Blocked'), ('no', 'Active')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
