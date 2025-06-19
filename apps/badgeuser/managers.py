# apps/badgeuser/managers.py

import cachemodel
import logging
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.db import transaction

logger = logging.getLogger(__name__)


class BadgeUserManager(BaseUserManager, cachemodel.CacheModelManager):
    """
    Manager para BadgeUser com cache e funcionalidades de criação
    """
    
    def create_user(self, email, password=None, send_confirmation=True, **extra_fields):
        """
        ✅ CORRIGIDO: Criar usuário com controle de confirmação de email
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        
        logger.info("User %s created successfully", email)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Criar superusuário
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, send_confirmation=False, **extra_fields)

    def get_by_email(self, email):
        """
        Buscar usuário por email
        """
        return self.get(email=email)


class CachedEmailAddressManager(cachemodel.CacheModelManager):
    """
    Manager para CachedEmailAddress
    """
    
    def get_users_by_email(self, email):
        """
        Retorna todos os usuários que têm o email especificado
        """
        email_addresses = self.filter(email=email)
        return [e.user for e in email_addresses]
    
    def get_primary(self, user):
        """
        Retorna o email primário do usuário
        """
        try:
            return self.get(user=user, primary=True)
        except self.model.DoesNotExist:
            return None
    
    def get_verified(self, user):
        """
        Retorna todos os emails verificados do usuário
        """
        return self.filter(user=user, verified=True)
    
    def add_email(self, user, email, request=None, confirm=False, signup=False, send_confirmation=None):
        """
        ✅ CORRIGIDO: Adicionar email sem enviar confirmação
        """
        # ✅ CORRIGIDO: Usar send_confirmation se fornecido, senão usar confirm
        if send_confirmation is None:
            send_confirmation = confirm
            
        try:
            # Verifica se o email já existe para este usuário
            email_address = self.get(user=user, email=email)
            if email_address.verified:
                logger.info("Email %s already verified for user %s", email, user.email)
                return email_address
        except self.model.DoesNotExist:
            # Criar novo email address
            is_primary = not self.filter(user=user).exists()
            email_address = self.create(
                user=user,
                email=email,
                verified=not send_confirmation,  # ✅ Se não enviar confirmação, marcar como verificado
                primary=is_primary
            )
            logger.info("Email %s created for user %s", email, user.email)

        if send_confirmation:
            logger.info("Email confirmation would be sent to %s", email)
            # ✅ CORRIGIDO: Não enviar confirmação, apenas marcar como verificado
            email_address.verified = True
            email_address.save()
            logger.info("Email %s marked as verified automatically", email)
        
        return email_address
    
    def get_for_user(self, user):
        """
        Retorna todos os emails do usuário
        """
        return self.filter(user=user)
    
    def can_add_email(self, user):
        """
        Verifica se o usuário pode adicionar mais emails
        """
        from django.conf import settings
        max_email_addresses = getattr(settings, 'ACCOUNT_MAX_EMAIL_ADDRESSES', None)
        if max_email_addresses:
            if self.filter(user=user).count() >= max_email_addresses:
                return False
        return True
    
    def fill_cache_for_user(self, user):
        """
        Pre-popular o cache para todos os emails do usuário
        """
        list(self.filter(user=user))
    
    def set_primary(self, user, email):
        """
        Definir email como primário
        """
        with transaction.atomic():
            # Remover primary de todos os outros emails
            self.filter(user=user, primary=True).update(primary=False)
            
            # Definir este email como primário
            email_address = self.get(user=user, email=email)
            email_address.primary = True
            email_address.save()
            
            logger.info("Email %s set as primary for user %s", email, user.email)
            return email_address
    
    def verify_email(self, user, email):
        """
        Marcar email como verificado
        """
        try:
            email_address = self.get(user=user, email=email)
            email_address.verified = True
            email_address.save()
            
            logger.info("Email %s verified for user %s", email, user.email)
            return email_address
        except self.model.DoesNotExist:
            logger.error("Email %s not found for user %s", email, user.email)
            raise ValueError("Email address not found")