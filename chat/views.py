from django.db.models import Q, Max, Count, Case, When, Value, IntegerField, F
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Message, make_room
from .serializers import MessageOutSerializer, PeerSerializer

User = get_user_model()

class ConversationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        me = request.user

        # Mensajes donde participo
        qs = Message.objects.filter(Q(sender=me) | Q(receiver=me))

        # peer_id: si yo soy sender → receiver_id; si no → sender_id
        peer_id_expr = Case(
            When(sender=me, then=F('receiver_id')),
            default=F('sender_id'),
            output_field=IntegerField()
        )

        # último timestamp por peer
        last_by_peer = (
            qs.annotate(peer_id=peer_id_expr)
                .values('peer_id')
                .annotate(last_ts=Max('timestamp'))
                .order_by('-last_ts')
        )

        peer_ids = [row['peer_id'] for row in last_by_peer]
        peers = {u.id: u for u in User.objects.filter(id__in=peer_ids)}

        # no leídos (si tienes read_at)
        unread_counts = (
            Message.objects.filter(receiver=me, read_at__isnull=True, sender_id__in=peer_ids)
            .values('sender_id')
            .annotate(c=Count('id'))
        )
        unread_map = {row['sender_id']: row['c'] for row in unread_counts}

        out = []
        for row in last_by_peer:
            pid = row['peer_id']
            peer = peers.get(pid)
            if not peer:
                continue

            # último mensaje concreto
            last_msg = (
                Message.objects
                .filter(
                    (Q(sender=me, receiver_id=pid) | Q(sender_id=pid, receiver=me))
                )
                .order_by('-timestamp')
                .first()
            )

            out.append({
                "peer": PeerSerializer(peer).data,
                "last_message": {
                    "id": last_msg.id if last_msg else None,
                    "text": last_msg.content if last_msg else "",
                    "created_at": last_msg.timestamp.isoformat() if last_msg else None,
                    "sender_id": last_msg.sender_id if last_msg else None,
                },
                "unread": unread_map.get(pid, 0),
            })

        return Response(out, status=200)


class MessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        me = request.user
        try:
            peer_id = int(request.query_params.get('peer_id'))
        except (TypeError, ValueError):
            return Response({'detail': 'peer_id requerido'}, status=400)

        limit = int(request.query_params.get('limit', 50))
        before = request.query_params.get('before')  # ISO opcional

        base_q = Q(sender_id=me.id, receiver_id=peer_id) | Q(sender_id=peer_id, receiver_id=me.id)
        qs = Message.objects.filter(base_q).order_by('-timestamp')

        if before:
            # parse_datetime puede usarse, pero como timestamp es auto_now_add, Now TZ aware:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(before)
            if dt is not None:
                qs = qs.filter(timestamp__lt=dt)

        items = list(qs[:max(1, min(limit, 200))])
        items = list(reversed(items))  # ascendente

        data = MessageOutSerializer(items, many=True).data
        return Response(data, status=200)

    def post(self, request):
        """
        Fallback HTTP para enviar mensaje (además del WS).
        """
        me = request.user
        try:
            peer_id = int(request.data.get('peer_id'))
        except (TypeError, ValueError):
            return Response({'detail': 'peer_id inválido'}, status=400)

        text = (request.data.get('text') or '').strip()
        if not text:
            return Response({'detail': 'text requerido'}, status=400)

        try:
            peer = User.objects.get(id=peer_id)
        except User.DoesNotExist:
            return Response({'detail': 'peer no encontrado'}, status=404)

        room = make_room(me.id, peer_id)
        msg = Message.objects.create(sender=me, receiver=peer, content=text, room_name=room)
        return Response(MessageOutSerializer(msg).data, status=201)


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        me = request.user
        try:
            peer_id = int(request.data.get('peer_id'))
        except (TypeError, ValueError):
            return Response({'detail': 'peer_id requerido'}, status=400)

        updated = (
            Message.objects
            .filter(sender_id=peer_id, receiver=me, read_at__isnull=True)
            .update(read_at=now())
        )
        return Response({'updated': updated}, status=200)