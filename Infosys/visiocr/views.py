
# Create your views here.

from django.shortcuts import render
from django.http import JsonResponse
from .serializers import OCRDataSerializer
from .models import OCRData  # Import your model
import pytesseract
import cv2
import numpy as np
import re
import sqlite3

# Configure Tesseract executable path

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(img, enable_preprocessing=True):
    if not enable_preprocessing:
        return img
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, threshed = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((1, 1), np.uint8)
    processed_img = cv2.dilate(threshed, kernel, iterations=1)
    return processed_img

def perform_ocr(img):
    try:
        text = pytesseract.image_to_string(img, lang='eng+hin')
        return text.strip()
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ""

def identify_document_type(text):
    pan_pattern = r'[A-Z]{5}\d{4}[A-Z]{1}'
    aadhaar_pattern = r'\d{4}\s\d{4}\s\d{4}'
    if re.search(pan_pattern, text):
        return "PAN Card"
    elif re.search(aadhaar_pattern, text):
        return "Aadhaar Card"
    else:
        return "Unknown"

def extract_pan_details(text):
    pan_number_pattern = r'[A-Z]{5}\d{4}[A-Z]{1}'
    name_pattern = r'(?:Name\s*:\s*|IH name\s*|Name\s*|Father\'s Name\s*:\s*)([A-Z\s]+)'
    dob_pattern = r'(\d{2}/\d{2}/\d{4})'
    pan_number = re.search(pan_number_pattern, text).group(0) if re.search(pan_number_pattern, text) else "Not Found"
    name = re.search(name_pattern, text).group(1).strip() if re.search(name_pattern, text) else "Not Found"
    dob = re.search(dob_pattern, text).group(1) if re.search(dob_pattern, text) else "Not Found"
    return {"Document Type": "PAN Card", "ID Number": pan_number, "Name": name, "Date of Birth": dob}

def extract_aadhaar_details(text):
    aadhaar_pattern = r'\d{4}\s\d{4}\s\d{4}'
    name_pattern = r'([A-Z][a-z]+\s[A-Z][a-z]+)'
    dob_pattern = r'(\d{2}/\d{2}/\d{4})'
    id_number = re.search(aadhaar_pattern, text).group(0) if re.search(aadhaar_pattern, text) else "Not Found"
    person_name = re.search(name_pattern, text).group(0).strip() if re.search(name_pattern, text) else "Not Found"
    dob = re.search(dob_pattern, text).group(1) if re.search(dob_pattern, text) else "Not Found"
    return {"Document Type": "Aadhaar Card", "ID Number": id_number, "Name": person_name, "Date of Birth": dob}

def extract_information(text):
    doc_type = identify_document_type(text)
    if doc_type == "PAN Card":
        return extract_pan_details(text)
    elif doc_type == "Aadhaar Card":
        return extract_aadhaar_details(text)
    else:
        return {"Document Type": "Unknown", "ID Number": "Not Found", "Name": "Not Found", "Date of Birth": "Not Found"}

def prompt_for_missing_data(data):
    for key, value in data.items():
        if value == "Not Found":
            user_input = input(f"{key} is missing. Please enter the {key}: ")
            data[key] = user_input.strip()
    return data

def store_data_in_db(data):
    print("Storing data:", data)
    ocr_data = OCRData(
        document_type=data["Document Type"],
        id_number=data["ID Number"],
        name=data["Name"],
        dob=data["Date of Birth"]
    )
    ocr_data.save()  # Use Django's save method


def upload_image(request):
    if request.method == 'POST' and request.FILES['document']:
        image_file = request.FILES['document']
        np_image = np.frombuffer(image_file.read(), np.uint8)
        img = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        
        # Assuming preprocess_image, perform_ocr, extract_information, and prompt_for_missing_data are defined as per your code
        processed_img = preprocess_image(img)
        
        # Perform OCR
        text = perform_ocr(processed_img)
        
        # Extract information
        data = extract_information(text)
        
        # Print extracted data for debugging
        print("Extracted data before filling missing values:", data)
        
        # Prompt user to fill in missing values manually
        data = prompt_for_missing_data(data)
        
        # Print final data after manual input
        print("Final data after user input:", data)
        
        # Store the data in the database
        store_data_in_db(data)

        # Verify that data was stored successfully
        all_data = OCRData.objects.all()  # Retrieve all records from the OCRData model
        print("All stored OCR data:")
        for record in all_data:
            print(f"Document Type: {record.document_type}, ID Number: {record.id_number}, Name: {record.name}, DOB: {record.dob}")

        return JsonResponse(data)

    return render(request, 'upload.html')

