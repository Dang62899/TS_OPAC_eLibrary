import base64
import io
import math
import random
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.cache import cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from .models import User


def _ordered_rect(x0, y0, x1, y1):
    """Return a rectangle tuple with the left/top bound guaranteed to be <= right/bottom."""
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def _warp_text_layer(text_layer, amplitude):
    """Apply a subtle wave distortion to a text layer for a classic CAPTCHA feel."""
    width, height = text_layer.size
    warped = Image.new("RGBA", text_layer.size, (255, 255, 255, 0))
    source = text_layer.load()
    target = warped.load()

    for y in range(height):
        wave = int(math.sin((y / max(height - 1, 1)) * math.pi * 2.2) * amplitude)
        for x in range(width):
            source_x = max(0, min(width - 1, x + wave))
            target[x, y] = source[source_x, y]

    return warped


def build_login_challenge():
    """Create a classic warped-word CAPTCHA image challenge with a readable answer token."""
    samples = [
        "A7K2",
        "M3P9",
        "Q8R1",
        "L4X6",
    ]
    correct_value = random.choice(samples)

    image = Image.new("RGB", (420, 150), color=(246, 246, 246))
    draw = ImageDraw.Draw(image)

    for _ in range(4):
        x0 = random.randint(20, 380)
        y0 = random.randint(20, 120)
        x1 = random.randint(20, 380)
        y1 = random.randint(20, 120)
        draw.arc(
            _ordered_rect(x0, y0, x1, y1),
            start=random.randint(0, 180),
            end=random.randint(180, 360),
            fill=(225, 225, 225),
            width=1,
        )

    for _ in range(12):
        x0 = random.randint(0, 420)
        y0 = random.randint(0, 150)
        x1 = random.randint(0, 420)
        y1 = random.randint(0, 150)
        draw.ellipse(_ordered_rect(x0, y0, x1, y1), fill=(214, 214, 214))

    try:
        font = ImageFont.truetype("arial.ttf", 58)
    except OSError:
        font = ImageFont.load_default()

    text_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_draw.text((52, 24), correct_value, font=font, fill=(24, 43, 34, 255))

    shadow = Image.new("RGBA", image.size, (255, 255, 255, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.text((54, 26), correct_value, font=font, fill=(0, 0, 0, 28))

    text_layer = _warp_text_layer(text_layer, random.randint(4, 7))
    text_layer = text_layer.rotate(random.uniform(-4, 4), resample=Image.BICUBIC, expand=False)
    text_layer = text_layer.filter(ImageFilter.SMOOTH)

    overlay = Image.alpha_composite(image.convert("RGBA"), shadow).convert("RGBA")
    overlay = Image.alpha_composite(overlay, text_layer)

    base = overlay.convert("RGB")
    base = base.filter(ImageFilter.GaussianBlur(radius=0.05))

    buffer = io.BytesIO()
    base.save(buffer, format="PNG")
    image_data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "correct_value": correct_value,
        "samples": samples,
        "image_data_url": image_data_url,
    }


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone", "address", "date_of_birth")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone", "address", "date_of_birth")


class BorrowerRegistrationForm(UserCreationForm):
    """Form for registering new borrowers"""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "phone",
            "address",
            "date_of_birth",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "borrower"
        if commit:
            user.save()
        return user


class AdminRegistrationForm(UserCreationForm):
    """Form for registering new staff or admin users"""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPES, required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "phone",
            "address",
            "date_of_birth",
            "user_type",
        )

    def __init__(self, *args, **kwargs):
        allowed_types = kwargs.pop("allowed_types", None)
        super().__init__(*args, **kwargs)
        if allowed_types is not None:
            self.fields["user_type"].choices = [choice for choice in User.USER_TYPES if choice[0] in allowed_types]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.cleaned_data.get("user_type", "borrower")
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Login form with CAPTCHA and optional TOTP challenge."""

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your User Name",
                "autocomplete": "username",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        )
    )
    captcha = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter CAPTCHA",
                "autocomplete": "off",
            }
        ),
    )
    totp_code = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Authenticator code",
                "autocomplete": "one-time-code",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_captcha(self):
        expected = None
        if self.request and hasattr(self.request, "session"):
            expected = self.request.session.get("login_captcha_value")
        if expected is None:
            expected = cache.get("login_captcha")

        submitted = (self.cleaned_data.get("captcha") or "").strip().lower()
        expected_value = str(expected).strip().lower() if expected is not None else ""
        if not expected_value or submitted != expected_value:
            raise forms.ValidationError("Invalid CAPTCHA challenge response.")
        return submitted


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "address", "date_of_birth")
