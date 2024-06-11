import fitz  # PyMuPDF
import cv2 as cv
import numpy as np
import copy
import time
import os


def convert_pdf_to_images(pdf_path, dpi=300):
    pdf_document = fitz.open(pdf_path)
    image_list = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap(dpi=dpi)
        image_data = pix.tobytes("png")
        image = cv.imdecode(np.frombuffer(image_data, np.uint8), cv.IMREAD_COLOR)
        image_list.append(image)

    return image_list


def detect_qr_in_image(image):
    qr_detector = cv.QRCodeDetector()
    data, points, _ = qr_detector.detectAndDecode(image)
    return data, points


def draw_tags(image, qrcode_result, elapsed_time):
    if qrcode_result[0]:
        text = qrcode_result[0]
        points = qrcode_result[1]

        if points is not None:
            points = points[0]
            for i in range(len(points)):
                pt1 = tuple(map(int, points[i]))
                pt2 = tuple(map(int, points[(i + 1) % len(points)]))
                cv.line(image, pt1, pt2, (0, 255, 0), 3)

        # Put the QR data text on the image
        cv.putText(image, text, (int(points[0][0]), int(points[0][1]) - 10), cv.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Display elapsed time
    cv.putText(image, f"Elapsed Time: {elapsed_time * 1000:.1f} ms", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv.LINE_AA)
    return image


def resize_image_to_fit_screen(image, screen_width, screen_height):
    height, width = image.shape[:2]
    scaling_factor = min(screen_width / width, screen_height / height)
    new_size = (int(width * scaling_factor), int(height * scaling_factor))
    resized_image = cv.resize(image, new_size, interpolation=cv.INTER_AREA)
    return resized_image


def analyze_pdf(pdf_path, output_folder, screen_width=1280, screen_height=720):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    images = convert_pdf_to_images(pdf_path)
    qr_detected = False
    qr_detected_pages = []

    for page_num, image in enumerate(images, start=1):
        start_time = time.time()
        qrcode_result = detect_qr_in_image(image)
        elapsed_time = time.time() - start_time

        debug_image = draw_tags(copy.deepcopy(image), qrcode_result, elapsed_time)
        resized_image = resize_image_to_fit_screen(debug_image, screen_width, screen_height)

        if qrcode_result[0]:
            qr_detected = True
            qr_detected_pages.append(os.path.join(output_folder, f"page_{page_num}.png"))
            cv.imwrite(qr_detected_pages[-1], resized_image)
            print(f"Page {page_num} - QR detected: {qrcode_result[0]}")
        else:
            print(f"Page {page_num} - No QR code detected.")

    if qr_detected:
        return "QR code detected in the PDF.", qr_detected_pages
    else:
        return "Good to go! No QR code found in the PDF.", []
