import os
import io
import base64
import zipfile
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as xlImage
from PIL import Image as PILImage
from PIL import ImageChops

TEMPLATE_PATH = "public/template.xlsx"

def base64_to_image(b64_str):
    if "," in b64_str:
        b64_str = b64_str.split(",")[1]
    img_data = base64.b64decode(b64_str)
    return PILImage.open(io.BytesIO(img_data))

def process_signature_centered(b64_str, target_w, target_h):
    """
    1. 서명의 여백(흰색 바탕)을 최소화하기 위해 Bounding Box 단위로 자름
    2. 목표 셀 크기(target_w, target_h)에 맞춰 종횡비를 유지하며 축소(thumbnail)
    3. 목표 셀 크기와 정확히 일치하는 흰색 배경의 캔버스를 만들고 가운데에 붙여넣음
    결과적으로 셀 내부에 딱 맞게 들어가는 가운데 정렬된 이미지를 생성.
    """
    img_pil = base64_to_image(b64_str)
    
    # 1. 흰색 배경(여백) 잘라내기
    img_rgb = img_pil.convert("RGB")
    bg = PILImage.new("RGB", img_rgb.size, (255, 255, 255))
    diff = ImageChops.difference(img_rgb, bg)
    bbox = diff.getbbox()
    if bbox:
        img_pil = img_pil.crop(bbox)
        
    # 2. 비율 유지 맞춰 축소
    img_pil.thumbnail((target_w, target_h), PILImage.Resampling.LANCZOS)
    
    # 3. 셀 크기와 정확히 똑같은 흰색 캔버스 생성
    new_img = PILImage.new("RGBA", (target_w, target_h), (255, 255, 255, 255))
    
    # 가운데 정렬 좌표 계산
    paste_x = max(0, (target_w - img_pil.width) // 2)
    paste_y = max(0, (target_h - img_pil.height) // 2)
    new_img.paste(img_pil, (paste_x, paste_y))
    
    # 엑셀 이미지로 변환
    img_byte_arr = io.BytesIO()
    new_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    xl_img = xlImage(img_byte_arr)
    xl_img.width = target_w
    xl_img.height = target_h
    return xl_img

def generate_excel_or_zip(subject_name, subject_content, course_time, lecture_date, submitted_date, instructor_info, trainees):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template file not found at {TEMPLATE_PATH}")

    # 15명 단위로 분할
    chunk_size = 15
    trainee_chunks = [trainees[i:i + chunk_size] for i in range(0, max(1, len(trainees)), chunk_size)]
    
    files = []
    
    for idx, chunk in enumerate(trainee_chunks):
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
            # 강사 서명: 6cm x 높이 맞춤 -> 너비 약 227px, 높이 53px
            xl_img = process_signature_centered(instructor_sig, target_w=227, target_h=53)
            ws.add_image(xl_img, 'I27')
        
        row_start = 10
        for i, trainee in enumerate(chunk):
            row = row_start + i
            ws[f'A{row}'] = trainee.get("team", "")
            ws[f'C{row}'] = trainee.get("employee_id", "")
            ws[f'E{row}'] = trainee.get("name", "")
            
            trainee_sig = trainee.get("signature")
            if trainee_sig:
                # 훈련생 서명: 4cm x 0.85cm -> 너비 약 151px, 높이 32px
                t_xl_img = process_signature_centered(trainee_sig, target_w=151, target_h=32)
                ws.add_image(t_xl_img, f'H{row}')

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        files.append((f"Report_Part{idx+1}.xlsx" if len(trainee_chunks) > 1 else "Report.xlsx", output.getvalue()))
        
    if len(files) == 1:
        return files[0][1], "xlsx"
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_name, file_bytes in files:
                zf.writestr(file_name, file_bytes)
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), "zip"
