
from django.views.generic import DetailView

from .models import Snippet


class SnippetDetailView(DetailView):
    model = Snippet
    template_name = "TEMPLATE_NAME"
