class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost:3306/testing'
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
