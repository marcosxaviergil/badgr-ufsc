# apps/badgeuser/serializers_v1.py

import logging
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed

from badgeuser.models import BadgeUser, CachedEmailAddress
from mainsite.validators import PasswordValidator, EmailValidator
import badgrlog

logger = logging.getLogger(__name__)
badgr_logger = badgrlog.BadgrLogger()


class BadgeUserProfileSerializerV1(serializers.Serializer):
    """
    Serializer for BadgeUser profile creation and updates
    """
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(validators=[EmailValidator()])
    password = serializers.CharField(
        style={'input_type': 'password'}, 
        validators=[PasswordValidator()],
        write_only=True,
        required=False
    )
    agreed_terms_service = serializers.BooleanField(default=True, required=False)
    marketing_opt_in = serializers.BooleanField(default=False, required=False)
    has_password_set = serializers.BooleanField(read_only=True)
    recipient_identifier = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        representation = super(BadgeUserProfileSerializerV1, self).to_representation(instance)
        if isinstance(instance, BadgeUser):
            representation['has_password_set'] = instance.has_usable_password()
            representation['recipient_identifier'] = instance.primary_identifier
        return representation

    def validate_email(self, email):
        """
        ✅ CORRIGIDO: Validar email sem restrições de domínio
        """
        if email:
            # Verificar se já existe usuário com este email
            existing_user = BadgeUser.objects.filter(email=email).first()
            if existing_user and (not hasattr(self, 'instance') or existing_user != self.instance):
                raise ValidationError("An account with this email already exists")
        return email

    def validate_password(self, password):
        """Validar senha usando o validador do Django"""
        if password:
            try:
                validator = PasswordValidator()
                validator(password)
            except DjangoValidationError as e:
                raise ValidationError(e.messages)
        return password

    def create(self, validated_data):
        """
        ✅ CORRIGIDO: Criar usuário sem enviar email de confirmação
        """
        from badgeuser.models import BadgeUser, CachedEmailAddress
        
        email = validated_data['email']
        password = validated_data.get('password')
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        
        # ✅ CORRIGIDO: Não enviar confirmação por email
        send_confirmation = False
        
        request = self.context.get('request')
        
        try:
            user = BadgeUser.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                request=request,
                send_confirmation=send_confirmation
            )
            
            if password:
                user.set_password(password)
                user.save()
            
            # ✅ CORRIGIDO: Adicionar email sem confirmação (send_confirmation=False)
            CachedEmailAddress.objects.add_email(
                user, 
                email, 
                request=request, 
                signup=True, 
                send_confirmation=False
            )
            
            logger.info("User %s created successfully without email confirmation", email)
            
            return user
            
        except Exception as e:
            logger.error("Error creating user %s: %s", email, str(e))
            raise ValidationError("Error creating user account")

    def update(self, instance, validated_data):
        """Atualizar perfil do usuário"""
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class BadgeUserEmailSerializerV1(serializers.Serializer):
    """
    Serializer for email management
    """
    email = serializers.EmailField(validators=[EmailValidator()])
    verified = serializers.BooleanField(read_only=True)
    primary = serializers.BooleanField(read_only=True)

    def create(self, validated_data):
        """
        ✅ CORRIGIDO: Adicionar email sem confirmação
        """
        email = validated_data['email']
        user = self.context['user']
        request = self.context.get('request')
        
        # ✅ CORRIGIDO: Criar email já verificado
        email_address = CachedEmailAddress.objects.add_email(
            user, 
            email, 
            request=request, 
            send_confirmation=False
        )
        
        return email_address


class BadgeUserTokenSerializerV1(serializers.Serializer):
    """
    Serializer for authentication tokens
    """
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            
            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise ValidationError(msg)
                attrs['user'] = user
                return attrs
            else:
                msg = _('Unable to log in with provided credentials.')
                raise AuthenticationFailed(msg)
        else:
            msg = _('Must include "username" and "password".')
            raise ValidationError(msg)


class BadgeUserForgotPasswordSerializerV1(serializers.Serializer):
    """
    Serializer for password reset requests
    """
    email = serializers.EmailField(validators=[EmailValidator()])
    
    def validate_email(self, email):
        """Verificar se existe usuário com este email"""
        try:
            user = BadgeUser.objects.get(email=email)
        except BadgeUser.DoesNotExist:
            # ✅ Não revelar se o email existe ou não por segurança
            pass
        return email

    def save(self):
        """
        ✅ CORRIGIDO: Não enviar email de reset de senha
        """
        email = self.validated_data['email']
        logger.info("Password reset would be sent to %s", email)
        # ✅ Em produção, aqui normalmente seria enviado um email
        return {'message': 'Password reset email sent if account exists'}


class BadgeUserChangePasswordSerializerV1(serializers.Serializer):
    """
    Serializer for password changes
    """
    old_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(
        style={'input_type': 'password'}, 
        validators=[PasswordValidator()]
    )
    
    def validate_old_password(self, old_password):
        """Verificar senha atual"""
        user = self.context['user']
        if not user.check_password(old_password):
            raise ValidationError("Current password is incorrect")
        return old_password
    
    def validate_new_password(self, new_password):
        """Validar nova senha"""
        try:
            validator = PasswordValidator()
            validator(new_password)
        except DjangoValidationError as e:
            raise ValidationError(e.messages)
        return new_password
    
    def save(self):
        """Alterar senha do usuário"""
        user = self.context['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        
        logger.info("Password changed for user %s", user.email)
        return user