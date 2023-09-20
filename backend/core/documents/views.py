from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import Document
from .serializers import DocumentSerializer


class GetDocumentsView(APIView):

    def get(self, request):
        """
        Returns all documents
        """
        documents = Document.objects.all()
        serializer = DocumentSerializer(documents, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
