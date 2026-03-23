import os
import io
import base64
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as xlImage
from PIL import Image as PILImage

TEMPLATE_PATH = "public/template.xlsx"

def base64_to_image(b64_str):
    if "," in b64_str:
        b64_str = b64_str.split(",")[1]
    img_data = base64.b64decode(b64_str)
    return PILImage.open(io.BytesIO(img_data))

def generate_excel_bytes(subject_name, subject_content, course_time, lecture_date, submitted_date,
                         instructor_info, trainees):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template file not found at {TEMPLATE_PATH}")

    wb = load_workbook(TEMPLATE_PATH)
    ws = wb.active

    ws['B3'] = subject_name
    ws['B4'] = subject_content
    ws['F5'] = course_time
    ws['B5'] = lecture_date if lecture_date else ""
    ws['C27'] = submitted_date if submitted_date else ""

    ws['I5'] = instructor_info.get("location", "")
    ws['B7'] = instructor_info.get("company", "")
    ws['F7'] = instructor_info.get("instructor_id", "")
    ws['I7'] = instructor_info.get("name", "")
    ws['F8'] = instructor_info.get("course_name", "")

    instructor_sig = instructor_info.get("signature")
    if instructor_sig:
        img_pil = base64_to_image(instructor_sig)
        img_byte_arr = io.BytesIO()
        img_pil.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        xl_img = xlImage(img_byte_arr)
        xl_img.width = 287
        xl_img.height = 109
        ws.add_image(xl_img, 'I27')
    
    row_start = 10
    for i, trainee in enumerate(trainees):
        if i >= 15:
            break
        row = row_start + i
        ws[f'A{row}'] = trainee.get("team", "")
        ws[f'C{row}'] = trainee.get("employee_id", "")
        ws[f'E{row}'] = trainee.get("name", "")
        
        trainee_sig = trainee.get("signature")
        if trainee_sig:
            t_img_pil = base64_to_image(trainee_sig)
            t_byte_arr = io.BytesIO()
            t_img_pil.save(t_byte_arr, format='PNG')
            t_byte_arr.seek(0)
            
            t_xl_img = xlImage(t_byte_arr)
            t_xl_img.width = 184
            t_xl_img.height = 33
            ws.add_image(t_xl_img, f'H{row}')

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
