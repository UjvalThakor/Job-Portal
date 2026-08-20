from django import forms
from .models import JobDescription


class SkillsListField(forms.CharField):
    """Accepts a comma-separated string in the form and stores/returns a list."""
    def to_python(self, value):
        if not value:
            return []
        return [s.strip() for s in value.split(',') if s.strip()]

    def prepare_value(self, value):
        if isinstance(value, list):
            return ', '.join(value)
        return value


class JobDescriptionForm(forms.ModelForm):
    required_skills = SkillsListField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, PostgreSQL'}),
        help_text="Comma-separated"
    )
    preferred_skills = SkillsListField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AWS, Docker'}),
        help_text="Comma-separated"
    )

    class Meta:
        model = JobDescription
        fields = ['title', 'department', 'description', 'required_skills', 'preferred_skills', 'min_experience_years']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'min_experience_years': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        }
