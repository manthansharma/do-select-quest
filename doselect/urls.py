from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static

from image_api import views

urlpatterns = [
    url(r'^generate-access-key/$', views.generate_auth_token),
    url(r'^regenerate-access-key/$', views.re_generate_auth_token),

    url(r'^api/image/$', views.ImageList.as_view()),
    url(r'^api/image/(?P<pk>[0-9]+)/$', views.ImageDetail.as_view()),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
