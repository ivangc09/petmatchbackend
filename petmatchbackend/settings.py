from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    #Terceros
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    "django_filters",

    #CORS para interacturar con React
    'corsheaders',
    'storages',

    'users',
    'pets',
    'chat',
    'channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    
]

CORS_ALLOW_ALL_ORIGINS = DEBUG
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://petmatchbackend-production.up.railway.app"
).split(",") if not DEBUG else []

ROOT_URLCONF = 'petmatchbackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# *                           *   
# *           REDIS           * 
# *                           *        
WSGI_APPLICATION = 'petmatchbackend.wsgi.application'
ASGI_APPLICATION = 'petmatchbackend.asgi.application'

REDIS_URL = os.getenv('REDIS_URL')

if REDIS_URL:
    if REDIS_URL.startswith("rediss://"):
        CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG": {
                    "hosts": [{"address": REDIS_URL, "ssl": True}],
                    "capacity": 1500,  
                    "expiry": 60 * 60,
                },
            }
        }
    else:
        CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG": {
                    "hosts": [REDIS_URL],
                    "capacity": 1500,
                    "expiry": 60 * 60,
                },
            }
        }
else:
    # Fallback para desarrollo sin Redis
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }



# *                                    *   
# *           BASES DE DATOS           * 
# *                                    *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

#BASE DE DATOS POSTGRESQL CON RAILWAY
if url := os.environ.get("DATABASE_URL"):
    DATABASES['default'] = dj_database_url.parse(
        url,
        conn_max_age=600,
        ssl_require=True 
    )



# *                                               *   
# *           CONFIGURACIONES DE DJANGO           * 
# *                                               *

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_USE_JWT = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SITE_ID = 1

ACCOUNT_LOGIN_METHODS = {'username'}

ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password1*', 'password2*','ciudad*','telefono*','tipo_usuario*']


SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('CLIENT_ID'),
            'secret': os.getenv('SECRET_KEY_GOOGLE'),
            'key': ''
        },
        'AUTH_PARAMS': {
            "access_type": "online",
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}
AUTH_USER_MODEL = 'users.CustomUser'

REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'users.serializers.CustomRegisterSerializer',
}

#CHANNEL_LAYERS = {
#    "default": {
#        "BACKEND": "channels_redis.core.RedisChannelLayer",
#        "CONFIG": {
#            "hosts": [REDIS_URL],
#        },
#    }
#}


ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
DEFAULT_FROM_EMAIL = 'no-reply@petmatch.loc'


# *                           *   
# *           S3              * 
# *                           *
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'us-east-2'

AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

DEFAULT_FILE_STORAGE = os.getenv('DEFAULT_FILE_STORAGE')
AWS_QUERYSTRING_AUTH = False

AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}