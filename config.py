"""Configuration for development environment"""
import os
from redis import Redis


class DevelopmentConfig():
    SECRET_KEY = 'application_by_yorch'
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5002
    SESSION_TYPE  = "redis"  # Guardar sesiones en Redis
    SESSION_PERMANENT  = False
    SESSION_USE_SIGNER  = True
    SESSION_KEY_PREFIX  = "session:"
    SESSION_REDIS  = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))  
    # Configuración de Cookies para que funcionen con ngrok y Vercel
    SESSION_COOKIE_SECURE  = True  # Requiere HTTPS
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = "None"  # Permite compartir cookies entre dominios
