
from django.conf.urls import url

from .views import BookDetailView

app_name = 'app_books'

urlpatterns = [
    url(r'book/(?P<slug>[_\w]+)/$', BookDetailView.as_view(), {}, 'book'),
]
