import os
from pathlib import Path
import dj_database_url  # pip install dj-database-url
from dotenv import load_dotenv
from urllib.parse import urlparse
# Load environment variables from .env (only used in local dev)
load_dotenv()

# --- Base Directory ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-fallback-secret-key')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Allow multiple comma-separated hosts: localhost,127.0.0.1,Meal_Buddy.onrender.com
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Default local development hosts
if not os.environ.get('ALLOWED_HOSTS'):
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Add Render external host if available
render_url = os.environ.get('RENDER_EXTERNAL_URL')
if render_url:
    parsed_url = urlparse(render_url)
    if parsed_url.hostname:
        ALLOWED_HOSTS.append(parsed_url.hostname)

# --- CSRF Settings ---
# CSRF trusted origins for production
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://meal-buddy-5dsz.onrender.com',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

# Add render URL to CSRF trusted origins if available
if render_url:
    CSRF_TRUSTED_ORIGINS.append(render_url)

# CSRF cookie settings
CSRF_COOKIE_SECURE = not DEBUG  # Use secure cookies in production
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access if needed
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# --- Applications ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'delivery',
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files for production
    'django.middleware.gzip.GZipMiddleware',       # Optional: Compress responses
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

# --- URLs & Templates ---
ROOT_URLCONF = 'meal_buddy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Update if you store templates outside app folders
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'meal_buddy.wsgi.application'

# --- Database ---
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Localization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static Files ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Primary Key Field Type ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Razorpay Integration ---
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

# --- Fixture Settings ---
# Disable automatic fixture loading to prevent Unicode errors
FIXTURE_DIRS = []

# --- Session Settings ---
# Session cookie settings for production
SESSION_COOKIE_SECURE = not DEBUG  # Use secure cookies in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours

# --- Security Settings ---
# Additional security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# --- Deployment Settings ---
# Ensure proper encoding for deployment
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# --- Optional: Logging (optional for debugging in prod) ---
if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': BASE_DIR / 'errors.log',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }
