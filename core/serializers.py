from rest_framework import serializers
from .models import Item
from .models import Reservation



class ItemSerializer(serializers.ModelSerializer):
    fee = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id',
            'item_no',
            'name',
            'description',
            'department',
            'quantity',
            'fee',               # calculated field
            'payment_type',      # required by ItemCard
            'custom_price',      # required by ItemCard
            'availability',
            'image',
        ]

    def get_fee(self, obj):
        return "Free" if obj.payment_type == "free" else str(obj.custom_price)

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

class ReservationSerializer(serializers.ModelSerializer):
    fee = serializers.SerializerMethodField()
    item_name = serializers.CharField(source='item.name')
    department = serializers.CharField(source='item.department')  # 👈 NEW
    image = serializers.SerializerMethodField()  # 👈 NEW

    class Meta:
        model = Reservation
        fields = [
            'id',
            'transaction_id',
            'item_name',
            'department',
            'image',
            'start_datetime',
            'end_datetime',
            'fee',
            'status',
        ]

    def get_fee(self, obj):
        return "Free" if obj.item.payment_type == "free" else str(obj.item.custom_price)

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.item.image and request:
            return request.build_absolute_uri(obj.item.image.url)
        return None
