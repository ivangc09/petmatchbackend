from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from dj_rest_auth.registration.views import RegisterView
from .serializers import CustomRegisterSerializer, ProfileSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

User = get_user_model()

class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer

class CustomLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'username y password requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
                'user': {
                    'email': getattr(user, "email", None),
                    'tipo_usuario': getattr(user, "tipo_usuario", None),
                    'username': getattr(user, "username", None),
                    'id': user.id,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
class PerfilUsuarioView(generics.RetrieveUpdateAPIView):
        serializer_class = ProfileSerializer
        permission_classes = [permissions.IsAuthenticated]
        parser_classes = (MultiPartParser, FormParser, JSONParser)

        def get_object(self):
            return self.request.user
        
        def update(self, request, *args, **kwargs):
            partial = request.method.lower() == 'patch'
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            
            instance.refresh_from_db()
            return Response(self.get_serializer(instance).data)
        
from rest_framework.decorators import api_view, permission_classes
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"ok": True})
