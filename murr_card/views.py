import logging


from django.db.models import Subquery, Count
from django.shortcuts import redirect
from django.urls import reverse

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from mptt.templatetags.mptt_tags import cache_tree_children


from murr_back.settings import LOCALHOST
from murr_comments.models import Comment
from murr_comments.serializers import CommentSerializer
from murr_rating.services import RatingActionsMixin, get_rating_query

from .models import MurrCard
from .serializers import MurrCardSerializers, EditorImageForMurrCardSerializers, AllMurrSerializer

from .services import generate_user_cover

logger = logging.getLogger(__name__)


class MurrPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'murr_card_len'
    max_page_size = 60


class MurrCardViewSet(RatingActionsMixin, ModelViewSet):
    serializer_class = AllMurrSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = MurrPagination

    def get_queryset(self):
        likes, dislikes = get_rating_query('MurrCard')
        queryset = MurrCard.objects.select_related('owner').annotate(
            rating=Count(Subquery(likes)) - Count(Subquery(dislikes))
        ).order_by('-timestamp')
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = MurrCardSerializers(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        request.data['owner'] = request.user.id
        request.data['cover'] = generate_user_cover(request.data.get('cover'))
        serializer = MurrCardSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        author = instance.owner.id
        login_user = request.user.id
        if author == login_user:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class EditorImageForMurrCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EditorImageForMurrCardSerializers(data=request.data)
        murr_dict = {"success": 0, "file": {"url": ""}}
        if serializer.is_valid():
            serializer.save()
            url = LOCALHOST + serializer.data['murr_editor_image']
            murr_dict = {"success": 1, "file": {"url": url}}
        return Response(murr_dict)
