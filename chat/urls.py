from django.urls import path
from .views import ConversationsView, MessagesView, MarkReadView

urlpatterns = [
    path('conversations/', ConversationsView.as_view(), name='chat-conversations'),
    path('messages/', MessagesView.as_view(), name='chat-messages'),
    path('read/', MarkReadView.as_view(), name='chat-read'),
]