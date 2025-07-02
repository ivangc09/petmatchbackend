from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from dj_rest_auth.registration.views import RegisterView
from .serializers import CustomRegisterSerializer, ProfileSerializer

User = get_user_model()

class CustomRegisterView(RegisterView):
    serializer_class = CustomRegisterSerializer

class CustomLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'tipo_usuario': user.tipo_usuario
                }
            })
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
class PerfilUsuarioView(generics.RetrieveUpdateAPIView):
        serializer_class = ProfileSerializer
        permission_classes = [permissions.IsAuthenticated]

        def get_object(self):
            return self.request.user
