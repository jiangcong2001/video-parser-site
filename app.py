import os
from flask import Flask
from src.api.parse import bp as api_bp
from src.api.download import bp as download_bp
from src.web.views import bp as web_bp
from configs.logging_config import get_logger

logger = get_logger(__name__)


def create_app(config=None):
    """应用工厂函数"""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
    if config:
        app.config.update(config)

    # 注册蓝图
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(download_bp, url_prefix='/api/download')
    app.register_blueprint(web_bp)

    return app


app = create_app()

# 让 gunicorn 能找到 `app`
application = app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8051))
    app.run(host='0.0.0.0', port=port, debug=False)
