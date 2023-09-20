import logging

from .base import *

INSTALLED_APPS += [
    'nplusone.ext.django',
]

# LOGGING = {
#     "version": 1,
#     "loggers": {
#         "django": {
#             "handlers": ["file"],
#             "level": "INFO"
#         }
#     },
#     "handlers": {
#         "file": {
#             "level": "INFO",
#             "class": "logging.handlers.RotatingFileHandler",
#             'filename': str(BASE_DIR) + "/logfile.log",
#             "formatter": "simple"
#         }
#     },
#     "formatters": {
#         "simple": {
#             "format": '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
#             "style": "{"
#         }
#     }
# }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '[{asctime}] {levelname} [{module}] {message}',
            'style': '{',
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(BASE_DIR) + "/logfile",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'MYAPP': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}


# simple JWT config
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('JWT',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

MIDDLEWARE += [
    'nplusone.ext.django.NPlusOneMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:1337",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001"
]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "w01a4471.kasserver.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "noreply@mima-poker.cc"
EMAIL_HOST_PASSWORD = "mimapokernoreply@#"
