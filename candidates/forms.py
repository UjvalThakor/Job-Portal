from django import forms
from .models import Resume, Candidate


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx,.png,.jpg,.jpeg'}),
        }


class CandidateEditForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['full_name', 'email', 'phone', 'address']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in
                   ['full_name', 'email', 'phone', 'address']}
