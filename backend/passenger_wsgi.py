import sys, os
# thư mục hiện tại là /home/<username>/backend
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app
application = app  # Passenger yêu cầu tên biến 'application'
