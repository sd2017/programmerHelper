
from django.utils.translation import ugettext_lazy as _
from django import forms

from suit.widgets import AutosizedTextarea
from apps.core.widgets import CKEditorAdminWidget

from utils.django.widgets import AdminImageThumbnail, SplitInputsArrayWidget

from apps.tags.forms import clean_tags

# from .models import Article, Subsection


class ArticleAdminModelForm(forms.ModelForm):
    """

    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs['class'] = 'span12'
        self.fields['name'].widget.attrs['placeholder'] = _('Enter name')

        self.fields['slug'].disabled = True
        self.fields['slug'].widget.attrs['class'] = 'span12'

        self.fields['user'].widget.widget.attrs['class'] = 'span11'

        # field 'links'
        widget_base_field = self.fields['links'].base_field.widget
        count_inputs = self.fields['links'].max_length
        self.fields['links'].widget = SplitInputsArrayWidget(
            widget_base_field,
            count_inputs,
            attrs={'class': 'span12'}
        )

        self.fields['quotation'].widget = AutosizedTextarea(attrs={
            'class': 'span12',
            'placeholder': _('Enter quotation'),
        })

    class Meta:
        widgets = {
            'status': forms.RadioSelect(),
            'image': AdminImageThumbnail(),
            'heading': CKEditorAdminWidget(),
            'conclusion': CKEditorAdminWidget(),
        }

    def clean_tags(self):

        super().clean()

        cleaned_tags = clean_tags(self)
        return cleaned_tags


class SubsectionAdminModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs['class'] = 'span12'
        self.fields['name'].widget.attrs['placeholder'] = _('Enter name')

        self.fields['slug'].disabled = True
        self.fields['slug'].widget.attrs['class'] = 'span12'

    class Meta:
        widgets = {
            'content': CKEditorAdminWidget(),
        }
