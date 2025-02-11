from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from rest_framework.routers import DefaultRouter

from .views import MurrCardViewSet, EditorImageForMurrCardView

router = DefaultRouter()
router.register('', MurrCardViewSet)

urlpatterns = [
    path('save_editor_image/', csrf_exempt(EditorImageForMurrCardView.as_view()), name='save_editor_image'),
]

urlpatterns += router.urls
