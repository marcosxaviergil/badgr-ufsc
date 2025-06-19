# apps/mainsite/validators.py

import re
import json
import base64
from datetime import datetime
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator as DjangoEmailValidator
from django.utils.translation import ugettext_lazy as _
from django.utils.deconstruct import deconstructible


@deconstructible
class PasswordValidator(object):
    """
    Valida senhas seguindo critérios de segurança do Badgr
    """
    def __init__(self, min_length=8):
        self.min_length = min_length

    def __call__(self, password):
        if len(password) < self.min_length:
            raise ValidationError(
                _('Password must be at least %(min_length)d characters long.'),
                code='password_too_short',
                params={'min_length': self.min_length}
            )
        return password


@deconstructible
class EmailValidator(object):
    """
    Valida endereços de email de forma simples
    Compatível com OAuth UFSC que aceita qualquer domínio
    """
    
    def __init__(self):
        # Regex simplificado para validação de email básica
        self.regex = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    def __call__(self, email):
        if not email:
            raise ValidationError(
                _('Email address is required.'),
                code='email_required'
            )
        
        if not self.regex.match(email):
            raise ValidationError(
                _('Enter a valid email address.'),
                code='invalid_email'
            )
        
        return email
    
    def validate(self, email):
        """Método alternativo de validação"""
        return self.__call__(email)


@deconstructible
class ChoicesValidator(object):
    """
    Valida se um valor está presente numa lista de escolhas válidas
    """
    def __init__(self, choices):
        self.choices = choices
        if hasattr(choices, '__iter__'):
            # Se choices é uma lista de tuplas (value, label)
            self.valid_choices = [choice[0] if isinstance(choice, (list, tuple)) else choice for choice in choices]
        else:
            self.valid_choices = choices

    def __call__(self, value):
        if value not in self.valid_choices:
            raise ValidationError(
                _('Select a valid choice. %(value)s is not one of the available choices.'),
                code='invalid_choice',
                params={'value': value}
            )
        return value


@deconstructible
class ValidImageValidator(object):
    """
    Valida se o arquivo é uma imagem válida
    """
    VALID_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.svg']
    
    def __init__(self, max_size=None):
        self.max_size = max_size or 5 * 1024 * 1024  # 5MB padrão
    
    def __call__(self, image_file):
        if not image_file:
            return image_file
            
        # Verificar extensão
        if hasattr(image_file, 'name'):
            extension = image_file.name.lower().split('.')[-1] if '.' in image_file.name else ''
            if f'.{extension}' not in self.VALID_EXTENSIONS:
                raise ValidationError(
                    _('File type not supported. Please upload a valid image file.'),
                    code='invalid_image_type'
                )
        
        # Verificar tamanho
        if hasattr(image_file, 'size') and image_file.size > self.max_size:
            raise ValidationError(
                _('File size too large. Maximum size allowed is %(max_size)s bytes.'),
                code='file_too_large',
                params={'max_size': self.max_size}
            )
        
        return image_file


@deconstructible
class URLValidator(RegexValidator):
    """
    Valida URLs de forma simples
    """
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    message = _('Enter a valid URL.')
    code = 'invalid_url'


@deconstructible
class BadgeExtensionValidator(object):
    """
    Validator para extensões de badge conforme Open Badges 2.0
    """
    def __init__(self, message=None):
        self.message = message or _('Invalid badge extension format.')

    def __call__(self, value):
        """
        Valida extensões de badge conforme especificação Open Badges 2.0
        """
        if not value:
            return value
        
        # Validação básica para extensões - deve ser um dict ou JSON válido
        if isinstance(value, dict):
            return self._validate_extension_dict(value)
        elif isinstance(value, str):
            try:
                parsed = json.loads(value)
                return self._validate_extension_dict(parsed)
            except (json.JSONDecodeError, TypeError):
                raise ValidationError(
                    _('Badge extension must be valid JSON.'),
                    code='invalid_json'
                )
        else:
            raise ValidationError(
                self.message,
                code='invalid_extension'
            )
    
    def _validate_extension_dict(self, extension_dict):
        """Valida estrutura interna da extensão"""
        if not isinstance(extension_dict, dict):
            raise ValidationError(
                _('Badge extension must be a dictionary.'),
                code='invalid_extension_type'
            )
        
        # Verificar se contém as chaves básicas esperadas
        # Conforme Open Badges 2.0, extensões devem ter pelo menos um type
        if '@context' in extension_dict and 'type' not in extension_dict:
            raise ValidationError(
                _('Badge extension with @context must include type.'),
                code='missing_extension_type'
            )
        
        return extension_dict


@deconstructible
class Base64ImageValidator(object):
    """
    Valida se uma string é uma imagem válida em base64
    """
    VALID_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml']
    
    def __init__(self, max_size=None):
        self.max_size = max_size or 5 * 1024 * 1024  # 5MB padrão
    
    def __call__(self, value):
        if not value:
            return value
        
        # Verificar se é data URI válida
        if not value.startswith('data:'):
            raise ValidationError(
                _('Image must be a valid data URI.'),
                code='invalid_data_uri'
            )
        
        try:
            # Extrair header e dados
            header, data = value.split(',', 1)
            
            # Verificar se o tipo de mídia é válido
            mime_type = header.split(';')[0].replace('data:', '')
            if mime_type not in self.VALID_IMAGE_TYPES:
                raise ValidationError(
                    _('Unsupported image type: %(mime_type)s'),
                    code='unsupported_image_type',
                    params={'mime_type': mime_type}
                )
            
            # Verificar se é base64 válido
            decoded_data = base64.b64decode(data)
            
            # Verificar tamanho
            if len(decoded_data) > self.max_size:
                raise ValidationError(
                    _('Image size too large. Maximum size allowed is %(max_size)s bytes.'),
                    code='file_too_large',
                    params={'max_size': self.max_size}
                )
            
        except (ValueError, TypeError) as e:
            raise ValidationError(
                _('Invalid base64 image data.'),
                code='invalid_base64'
            )
        
        return value


@deconstructible
class SlugValidator(RegexValidator):
    """
    Valida slugs compatíveis com Badgr
    """
    regex = re.compile(r'^[a-zA-Z0-9_-]+$')
    message = _('Enter a valid slug consisting of letters, numbers, underscores or hyphens.')
    code = 'invalid_slug'


@deconstructible
class JSONValidator(object):
    """
    Valida se uma string é JSON válido
    """
    def __init__(self, message=None):
        self.message = message or _('Enter valid JSON.')
    
    def __call__(self, value):
        if not value:
            return value
        
        if isinstance(value, dict):
            return value
        
        try:
            json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise ValidationError(self.message, code='invalid_json')
        
        return value


@deconstructible
class EntityIdValidator(RegexValidator):
    """
    Valida entity IDs conforme padrão Badgr
    """
    regex = re.compile(r'^[a-zA-Z0-9_-]{22}$')
    message = _('Enter a valid entity ID.')
    code = 'invalid_entity_id'


@deconstructible
class ISODateValidator(object):
    """
    Valida datas no formato ISO 8601
    """
    def __init__(self, message=None):
        self.message = message or _('Enter a valid ISO 8601 date.')
    
    def __call__(self, value):
        if not value:
            return value
        
        try:
            # Tentar fazer parse da data ISO 8601
            if isinstance(value, str):
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif not isinstance(value, datetime):
                raise ValueError("Invalid date type")
        except ValueError:
            raise ValidationError(self.message, code='invalid_iso_date')
        
        return value


@deconstructible
class BadgeClassCriteriaValidator(object):
    """
    Valida critérios de BadgeClass conforme Open Badges 2.0
    """
    def __init__(self, message=None):
        self.message = message or _('Invalid badge criteria format.')
    
    def __call__(self, value):
        if not value:
            return value
        
        # Pode ser string (critérios narrativos) ou dict (critérios estruturados)
        if isinstance(value, str):
            # Verificar se não está vazio
            if not value.strip():
                raise ValidationError(
                    _('Criteria cannot be empty.'),
                    code='empty_criteria'
                )
        elif isinstance(value, dict):
            # Validar estrutura de critérios estruturados
            if 'narrative' not in value and 'id' not in value:
                raise ValidationError(
                    _('Structured criteria must include either narrative or id.'),
                    code='invalid_criteria_structure'
                )
        else:
            raise ValidationError(
                self.message,
                code='invalid_criteria_type'
            )
        
        return value


@deconstructible
class OpenBadgeTypeValidator(object):
    """
    Valida tipos de Open Badge conforme especificação 2.0
    """
    VALID_TYPES = [
        'BadgeClass',
        'Assertion', 
        'Issuer',
        'Profile',
        'IdentityObject',
        'VerificationObject',
        'Extension'
    ]
    
    def __init__(self, allowed_types=None):
        self.allowed_types = allowed_types or self.VALID_TYPES
    
    def __call__(self, value):
        if not value:
            return value
        
        # Pode ser string ou lista
        types_to_check = [value] if isinstance(value, str) else value
        
        for badge_type in types_to_check:
            if badge_type not in self.allowed_types:
                raise ValidationError(
                    _('Invalid badge type: %(type)s. Must be one of: %(valid_types)s'),
                    code='invalid_badge_type',
                    params={
                        'type': badge_type,
                        'valid_types': ', '.join(self.allowed_types)
                    }
                )
        
        return value


# Funções de conveniência para uso direto
def validate_password(password):
    """Função de conveniência para validar senhas"""
    validator = PasswordValidator()
    return validator(password)


def validate_email(email):
    """Função de conveniência para validar emails"""
    validator = EmailValidator()
    return validator(email)


def validate_choices(value, choices):
    """Função de conveniência para validar escolhas"""
    validator = ChoicesValidator(choices)
    return validator(value)


def validate_image(image_file):
    """Função de conveniência para validar imagens"""
    validator = ValidImageValidator()
    return validator(image_file)


def validate_url(url):
    """Função de conveniência para validar URLs"""
    validator = URLValidator()
    return validator(url)


def validate_badge_extension(extension):
    """Função de conveniência para validar extensões de badge"""
    validator = BadgeExtensionValidator()
    return validator(extension)


def validate_base64_image(image_data):
    """Função de conveniência para validar imagens base64"""
    validator = Base64ImageValidator()
    return validator(image_data)


def validate_slug(slug):
    """Função de conveniência para validar slugs"""
    validator = SlugValidator()
    return validator(slug)


def validate_json(json_data):
    """Função de conveniência para validar JSON"""
    validator = JSONValidator()
    return validator(json_data)


def validate_entity_id(entity_id):
    """Função de conveniência para validar entity IDs"""
    validator = EntityIdValidator()
    return validator(entity_id)


def validate_iso_date(date_value):
    """Função de conveniência para validar datas ISO"""
    validator = ISODateValidator()
    return validator(date_value)


def validate_badge_criteria(criteria):
    """Função de conveniência para validar critérios de badge"""
    validator = BadgeClassCriteriaValidator()
    return validator(criteria)


def validate_badge_type(badge_type):
    """Função de conveniência para validar tipos de badge"""
    validator = OpenBadgeTypeValidator()
    return validator(badge_type)
