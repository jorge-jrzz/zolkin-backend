BASE_DIR = "./app/"
UPLOAD_FOLDER = BASE_DIR + "files/uploads/"

class DevelopmentConfig():
    SECRET_KEY = 'application_by_yorch'
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5002
    UPLOAD_FOLDER = UPLOAD_FOLDER
