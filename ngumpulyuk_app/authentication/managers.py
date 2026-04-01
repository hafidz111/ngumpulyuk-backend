import re

from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError(_("Mohon masukkan email yang valid"))
        
    def create_user(self, email, full_name, password, **extra_fields):
        if email:
            email=self.normalize_email(email)
            self.email_validator(email)
        
        else:
            raise ValueError(_("Email harus diisi"))
        if not full_name:
            raise ValueError(_("Nama harus diisi"))
        if not extra_fields.get("username"):
            base = re.sub(r"[^a-zA-Z0-9_]", "_", (email or "").split("@")[0])[:30] or "user"
            base = base.strip("_") or "user"
            username = base
            for _ in range(200):
                if not self.model.objects.filter(username=username).exists():
                    break
                username = f"{base[:18]}_{get_random_string(8)}"
            extra_fields["username"] = username
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Staff harus bernilai true untuk admin"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser harus bernilai true untuk admin"))
        user=self.create_user(email, full_name, password, **extra_fields)
        user.save(using=self._db)
        return user