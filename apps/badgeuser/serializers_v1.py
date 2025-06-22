# apps/badgeuser/serializers_v1.py

from django.conf import settings
from django.contrib.auth.hashers import is_password_usable
from rest_framework import serializers
from collections import OrderedDict
from mainsite.models import BadgrApp
from mainsite.serializers import StripTagsCharField
from mainsite.validators import PasswordValidator
from .models import BadgeUser, CachedEmailAddress, TermsVersion
from .utils import notify_on_password_change


class BadgeUserTokenSerializerV1(serializers.Serializer):
    class Meta:
        apispec_definition = ('BadgeUserToken', {})

    def to_representation(self, instance):
        representation = {
            'username': instance.username,
            'token': instance.cached_token()
        }
        if self.context.get('tokenReplaced', False):
            representation['replace'] = True
        return representation

    def update(self, instance, validated_data):
        # noop
        return instance


class VerifiedEmailsField(serializers.Field):
    def to_representation(self, obj):
        addresses = []
        for emailaddress in obj.all():
            addresses.append(emailaddress.email)
        return addresses


class BadgeUserProfileSerializerV1(serializers.Serializer):
    first_name = StripTagsCharField(max_length=30, allow_blank=True)
    last_name = StripTagsCharField(max_length=30, allow_blank=True)
    email = serializers.EmailField(source='primary_email', read_only=True)  # ✅ CORRIGIDO: só read_only
    url = serializers.ListField(read_only=True, source='cached_verified_urls')
    telephone = serializers.ListField(read_only=True, source='cached_verified_phone_numbers')
    slug = serializers.CharField(source='entity_id', read_only=True)
    agreed_terms_version = serializers.IntegerField(required=False)
    marketing_opt_in = serializers.BooleanField(required=False)
    has_password_set = serializers.SerializerMethodField()
    source = serializers.CharField(write_only=True, required=False)

    def get_has_password_set(self, obj):
        return is_password_usable(obj.password)

    class Meta:
        apispec_definition = ('BadgeUser', {
            'properties': OrderedDict([
                ('source', {
                    'type': "string",
                    'format': "string",
                    'description': "Ex: mozilla",
                }),
            ])
        })

    def create(self, validated_data):
        # ✅ BLOQUEADO: Não permitir criação de usuário via API local
        raise serializers.ValidationError("Account creation is only available through institutional UFSC authentication.")

    def update(self, user, validated_data):
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        
        # ✅ BLOQUEADO: Não aceitar campos de senha
        if 'password' in validated_data or 'current_password' in validated_data:
            raise serializers.ValidationError("Password changes are managed through your institutional UFSC account.")

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        if 'agreed_terms_version' in validated_data:
            user.agreed_terms_version = validated_data.get('agreed_terms_version')

        if 'marketing_opt_in' in validated_data:
            user.marketing_opt_in = validated_data.get('marketing_opt_in')

        user.save()
        return user

    def to_representation(self, instance):
        representation = super(BadgeUserProfileSerializerV1, self).to_representation(instance)

        latest = TermsVersion.cached.cached_latest()
        if latest:
            representation['latest_terms_version'] = latest.version
            if latest.version != instance.agreed_terms_version:
                representation['latest_terms_description'] = latest.short_description

        return representation


class EmailSerializerV1(serializers.ModelSerializer):
    variants = serializers.ListField(
        child=serializers.EmailField(required=False),
        required=False, source='cached_variants', allow_null=True, read_only=True
    )
    email = serializers.EmailField(read_only=True)  # ✅ CORRIGIDO: removido required=True

    class Meta:
        model = CachedEmailAddress
        fields = ('id', 'email', 'verified', 'primary', 'variants')
        read_only_fields = ('id', 'email', 'verified', 'primary', 'variants')
        apispec_definition = ('BadgeUserEmail', {})

    def create(self, validated_data):
        # ✅ BLOQUEADO: Não permitir adição de email via API
        raise serializers.ValidationError("Email addresses are managed through your institutional UFSC account and cannot be modified here.")


class BadgeUserIdentifierFieldV1(serializers.CharField):
    def __init__(self, *args, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'created_by_id'
        if 'read_only' not in kwargs:
            kwargs['read_only'] = True
        super(BadgeUserIdentifierFieldV1, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        try:
            return BadgeUser.cached.get(pk=value).primary_email
        except BadgeUser.DoesNotExist:
            return None
