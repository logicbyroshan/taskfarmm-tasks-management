from django import forms
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import password_validation
from .models import Task, Category, UserProfile


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'category', 'priority', 'status', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter task title...',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'id': 'task-description-editor',
                'placeholder': 'Enter task description...',
                'class': 'form-control',
                'rows': 4,
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=user) | Q(members=user)
            ).distinct()
            self.fields['category'].empty_label = "No Category"


class CategoryForm(forms.ModelForm):
    board_template = forms.ChoiceField(
        choices=Category.BoardTemplate.choices,
        required=False,
        initial=Category.BoardTemplate.SMART,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Category
        fields = ['name', 'color', 'description', 'board_template']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Work, Personal, Health',
                'class': 'form-control'
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Optional project description...',
                'class': 'form-control',
                'rows': 2,
            }),
        }

    def clean_board_template(self):
        val = self.cleaned_data.get('board_template')
        return val or Category.BoardTemplate.SMART


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email:
            existing = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("This email address is already in use by another account.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if username:
            existing = User.objects.filter(username__iexact=username)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("This username is already taken.")
        return username


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'theme',
            'notify_task_reminders',
            'notify_due_date_alerts',
            'notify_app_updates',
            'default_task_priority',
            'default_task_status',
        ]
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'default_task_priority': forms.Select(attrs={'class': 'form-control'}),
            'default_task_status': forms.Select(attrs={'class': 'form-control'}),
        }


class PasswordUpdateForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username or email',
            'autofocus': True,
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=100,
        required=False,
        label="Full Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Alex Mercer',
            'autocomplete': 'name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password (min 6 chars)',
            'autocomplete': 'new-password'
        })
    )
    confirm_password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            })
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            else:
                user_instance = User(username=username, email=email)
                try:
                    password_validation.validate_password(password, user=user_instance)
                except forms.ValidationError as error:
                    self.add_error('password', error)

        return cleaned_data