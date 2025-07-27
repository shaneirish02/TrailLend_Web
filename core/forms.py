from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'image', 'custom_price', 'availability']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'fee': forms.NumberInput(attrs={'step': '0.01'}),
            'custom_price': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        custom_price = cleaned_data.get('custom_price')

        if payment_type == 'custom' and not custom_price:
            self.add_error('custom_price', 'Please provide a price for custom payment type.')

        if payment_type == 'free':
            cleaned_data['custom_price'] = None

        return cleaned_data
