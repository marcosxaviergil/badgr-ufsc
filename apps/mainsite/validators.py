# apps/mainsite/validators.py

import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _


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
