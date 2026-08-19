from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
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
            self.fields['category'].queryset = Category.objects.filter(user=user)
            self.fields['category'].empty_label = "No Category"


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color', 'description']
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