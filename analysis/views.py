from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from .forms import UploadFileForm
from .models import UploadedFile
from .utils import analyze_pdf
import os
import shutil
import uuid

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                uploaded_file = UploadedFile(file=request.FILES['file'])
                uploaded_file.save()
                return redirect('analyze_file', file_id=uploaded_file.id)
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Invalid form submission")
    else:
        form = UploadFileForm()
    return render(request, 'analysis/upload.html', {'form': form})

def analyze_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id)
    file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.file.name)
    output_folder = os.path.join(settings.MEDIA_ROOT, 'temp', str(file_id))

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    message, highlighted_pages = analyze_pdf(file_path, output_folder)
    highlighted_images_urls = []

    for image_path in highlighted_pages:
        base_name = os.path.basename(image_path)
        unique_name = f"{uuid.uuid4().hex}_{base_name}"
        destination = os.path.join(output_folder, unique_name)

        shutil.move(image_path, destination)
        highlighted_images_urls.append(os.path.join(settings.MEDIA_URL, 'temp', str(file_id), unique_name))

    return render(request, 'analysis/result.html', {'message': message, 'highlighted_images': highlighted_images_urls})
