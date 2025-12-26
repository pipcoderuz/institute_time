from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('roles', ['admin', 'teacher', 'student'])
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser, PermissionsMixin):
    objects = CustomUserManager()
    roles = models.JSONField(default=list)
    active_role = models.CharField(max_length=20, blank=True, null=True, default='student')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True, default='profiles/default-avatar.png')

    hemis_student_id = models.BigIntegerField(unique=True, null=True, blank=True)  # bogʻlash uchun

    def has_role(self, role):
        """Does have user role?"""
        return role in self.roles
    
    def add_role(self, role):
        """Add new role to user"""
        if role not in self.roles:
            self.roles.append(role)
            self.save()
    
    def remove_role(self, role):
        """Remove role from user"""
        if role in self.roles:
            self.roles.remove(role)
            self.save()
    
    def set_active_role(self, role):
        """Change active role"""
        if role in self.roles:
            self.active_role = role
            self.save()
            return True
        return False
            
    @property
    def is_student(self):
        return self.has_role('student')
    
    @property
    def is_teacher(self):
        return self.has_role('teacher')
    
    @property
    def is_admin(self):
        return self.has_role('admin')

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
