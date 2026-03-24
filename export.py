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

import zipfile

def generate_excel_or_zip(subject_name, subject_content, course_time, lecture_date, submitted_date, instructor_info, trainees):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template file not found at {TEMPLATE_PATH}")

    # 15명 단위로 훈련생 리스트 분할 (Chunk)
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
            img_pil = base64_to_image(instructor_sig)
            img_byte_arr = io.BytesIO()
            img_pil.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            xl_img = xlImage(img_byte_arr)
            # 강사 서명판 셀 크기 (I+J 병합)
            # 너비: 열 너비 34.6 char × 7px = 242px
            # 높이: 행 높이 40pt × (96/72) = 53px
            xl_img.width = 242
            xl_img.height = 53
            ws.add_image(xl_img, 'I27')
        
        row_start = 10
        for i, trainee in enumerate(chunk):
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
                # 훈련생 서명판 셀 크기 (H+I 병합)
                # 너비: 열 너비 21.7 char × 7px = 152px
                # 높이: 행 높이 25pt × (96/72) = 33px
                t_xl_img.width = 152
                t_xl_img.height = 33
                ws.add_image(t_xl_img, f'H{row}')

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # 파일명 지정 (여러 장일 경우 넘버링 추가)
        files.append((f"Report_Part{idx+1}.xlsx" if len(trainee_chunks) > 1 else "Report.xlsx", output.getvalue()))
        
    if len(files) == 1:
        # 1장이면 그냥 엑셀 파일 반환
        return files[0][1], "xlsx"
    else:
        # 2장 이상이면 ZIP 압축 반환
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_name, file_bytes in files:
                zf.writestr(file_name, file_bytes)
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), "zip"
