from django.contrib import admin
from django.urls import path, include
from visiocr.views import upload_image  # Import the upload_image view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ocr/', upload_image, name='upload_image'),  # Use your existing view
    path('', upload_image, name='upload_image'),  # Redirect root URL to the upload_image view
    path('ocr/', include('visiocr.urls')),  # Assuming 'visiocr' is your app name
]