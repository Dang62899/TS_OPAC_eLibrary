import base64
import io
import math
import random
from django import forms
from django.conf import settings
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


# Ambiguous characters (0/O, 1/I/L, 5/S, 2/Z, 8/B) are excluded so legitimate users can read the code.
CAPTCHA_ALPHABET = "ACDEFGHJKMNPQRTUVWXY34679"
CAPTCHA_FONTS = (
    "arialbd.ttf", "verdanab.ttf", "georgiab.ttf", "trebucbd.ttf", "timesbd.ttf", "courbd.ttf",
    "DejaVuSans-Bold.ttf", "DejaVuSerif-Bold.ttf",
)


def _load_captcha_font(size, rng):
    fonts = list(CAPTCHA_FONTS)
    rng.shuffle(fonts)
    for name in fonts:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_login_challenge():
    """Generate a fresh random captcha: per-character rotation, mixed fonts, wave warp and noise."""
    rng = random.SystemRandom()
    correct_value = "".join(rng.choice(CAPTCHA_ALPHABET) for _ in range(rng.choice((5, 6))))

    width, height = 420, 150
    image = Image.new("RGB", (width, height), color=(rng.randint(225, 245),) * 3)
    draw = ImageDraw.Draw(image)

    for _ in range(18):
        shade = rng.randint(150, 210)
        draw.line(
            (rng.randint(0, width), rng.randint(0, height), rng.randint(0, width), rng.randint(0, height)),
            fill=(shade, shade, shade),
            width=rng.randint(1, 3),
        )
    for _ in range(30):
        shade = rng.randint(170, 215)
        draw.ellipse(
            _ordered_rect(rng.randint(0, width), rng.randint(0, height), rng.randint(0, width), rng.randint(0, height)),
            fill=(shade, shade, shade),
        )

    text_layer = Image.new("RGBA", (width + 80, height + 40), (255, 255, 255, 0))
    slot = (width - 30) / len(correct_value)
    for index, char in enumerate(correct_value):
        size = rng.randint(66, 88)
        font = _load_captcha_font(size, rng)
        glyph = Image.new("RGBA", (size + 40, size + 40), (255, 255, 255, 0))
        dark = rng.randint(0, 60)
        ImageDraw.Draw(glyph).text(
            (16, 6), char, font=font, fill=(dark, dark, dark, 255), stroke_width=rng.choice((1, 2)), stroke_fill=(dark, dark, dark, 255)
        )
        glyph = glyph.rotate(rng.uniform(-25, 25), resample=Image.BICUBIC, expand=True)
        text_layer.alpha_composite(
            glyph, (int(40 + index * slot + rng.randint(-6, 6)), rng.randint(5, 45))
        )

    text_layer = _warp_text_layer(text_layer, rng.randint(8, 12))
    text_layer = text_layer.resize((width, height), resample=Image.BICUBIC)
    base = Image.alpha_composite(image.convert("RGBA"), text_layer)

    overlay = ImageDraw.Draw(base)
    for _ in range(7):
        shade = rng.randint(40, 110)
        points = [(rng.randint(0, width), rng.randint(20, height - 20)) for _ in range(3)]
        overlay.line(points, fill=(shade, shade, shade, 255), width=rng.randint(2, 3))
    for _ in range(200):
        px, py = rng.randint(0, width - 1), rng.randint(0, height - 1)
        shade = rng.randint(0, 255)
        overlay.point((px, py), fill=(shade, shade, shade, 255))

    base = base.convert("RGB").filter(ImageFilter.GaussianBlur(radius=0.6))

    buffer = io.BytesIO()
    base.save(buffer, format="PNG")
    image_data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "correct_value": correct_value,
        "samples": [],
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
    """Form for creating borrower/student accounts."""

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
    """Form for administrators to create user accounts."""

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
        user.is_staff = user.user_type in {"staff", "admin"}
        user.is_superuser = user.user_type == "admin"
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
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        ),
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


class AgreementAcceptanceForm(forms.Form):
    accept_agreement = forms.BooleanField(
        label="I have read and accept the user agreement and applicable SOPs.",
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "date_of_birth",
            "photo",
        )

    photo = forms.ImageField(required=False)

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo:
            max_size = int(getattr(settings, "MAX_PROFILE_PHOTO_SIZE_MB", 5)) * 1024 * 1024
            if photo.size > max_size:
                raise forms.ValidationError(
                    f"Profile photos must be no larger than {max_size // (1024 * 1024)} MB."
                )
        return photo
