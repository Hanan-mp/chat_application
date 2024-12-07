from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class CreateThreadForm(forms.Form):
    # Select another user to create a thread
  second_person = forms.ModelChoiceField(queryset=User.objects.all(),label="Select Contact", widget=forms.Select(attrs={'class': 'form-control'}),empty_label="Choose existing contact ")  # This will display the placeholder-like option in the dropdown)  # Adding custom attributes)
    
  def __init__(self, *args, **kwargs):
    user = kwargs.pop('user')  # The logged-in user
    super().__init__(*args, **kwargs)
    self.fields['second_person'].queryset = User.objects.exclude(id=user.id)  # Exclude current user
