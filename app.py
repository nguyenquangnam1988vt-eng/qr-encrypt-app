import streamlit as st
import qrcode
import json
from cryptography.fernet import Fernet
from hashlib import sha256
import base64
from PIL import Image
from io import BytesIO
import re

# ====== MẬT KHẨU MẶC ĐỊNH CHO CÔNG AN ======
DEFAULT_PASSWORD = "CA@123123"

# ====== Hàm mã hóa / giải mã ======
def generate_key(password: str) -> bytes:
    key = sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key[:32])

def encrypt_data(data: str, password: str) -> str:
    key = generate_key(password)
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(token: str, password: str) -> str:
    key = generate_key(password)
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()

# ====== Hàm tạo QR code ổn định ======
def create_stable_qr_code(data):
    """Tạo QR code ổn định"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# ====== Giao diện web ======
st.set_page_config(page_title="Hệ Thống QR Code Quản Lý Học Sinh", page_icon="🎓", layout="wide")

st.title("🎓 HỆ THỐNG QUẢN LÝ HỌC SINH THAM GIA GIAO THÔNG")
st.markdown("**Ứng dụng mã QR thông minh cho Công an, Nhà trường và Phụ huynh**")

tab1, tab2 = st.tabs(["📦 TẠO MÃ QR", "🔓 GIẢI MÃ THÔNG TIN"])

# ---------- TAB 1: TẠO MÃ QR ----------
with tab1:
    st.subheader("📋 NHẬP THÔNG TIN ĐỂ TẠO MÃ QR")
    
    st.markdown("### 🎯 CHỌN LOẠI ĐỐI TƯỢNG")
    loai_doituong = st.radio(
        "Loại xe:",
        [
            "🚗 XE CÁ NHÂN HỌC SINH",
            "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM", 
            "🏠 XE GIA ĐÌNH (chỉ thông tin chủ xe)"
        ],
        index=0
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if loai_doituong in ["🚗 XE CÁ NHÂN HỌC SINH", "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM"]:
            st.markdown("### 👤 THÔNG TIN HỌC SINH")
            hoten_hocsinh = st.text_input("Họ tên học sinh *", placeholder="Nguyễn Văn A")
            ngaysinh_hocsinh = st.text_input("Ngày sinh học sinh *", placeholder="15/07/2008")
            lop = st.text_input("Lớp", placeholder="10A1")
            truong = st.text_input("Trường", placeholder="THPT ABC")
        else:
            st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
            hoten_chuxe = st.text_input("Họ tên chủ xe *", placeholder="Nguyễn Văn B")
            ngaysinh_chuxe = st.text_input("Ngày sinh chủ xe *", placeholder="20/05/1975")
            sdt_chuxe = st.text_input("Số điện thoại chủ xe *", placeholder="0912345678")
    
    with col2:
        st.markdown("### 🚗 THÔNG TIN XE")
        bienso_xe = st.text_input("Biển số xe *", placeholder="59-A1 123.45")
        
        if loai_doituong == "🚗 XE CÁ NHÂN HỌC SINH":
            loai_xe = st.text_input("Loại xe", placeholder="Wave Alpha")
            mau_xe = st.text_input("Màu xe", placeholder="Đen")
            
        elif loai_doituong == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
            st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
            hoten_chuxe = st.text_input("Họ tên chủ xe *", placeholder="Nguyễn Văn B")
            ngaysinh_chuxe = st.text_input("Ngày sinh chủ xe *", placeholder="20/05/1975")
            sdt_chuxe = st.text_input("Số điện thoại chủ xe *", placeholder="0912345678")
            quanhe_voihocsinh = st.selectbox("Quan hệ với học sinh", 
                                           ["Bố", "Mẹ", "Ông", "Bà", "Anh", "Chị", "Khác"])
            
        else:  # XE GIA ĐÌNH
            loai_xe = st.text_input("Loại xe", placeholder="Vision")
            mau_xe = st.text_input("Màu xe", placeholder="Trắng")
    
    st.markdown("### 🔑 THIẾT LẬP MẬT KHẨU")
    col_pass1, col_pass2 = st.columns(2)
    
    with col_pass1:
        custom_password = st.text_input(
            "Mật khẩu tùy chỉnh *", 
            placeholder="Nhập mật khẩu để mở QR sau này",
            type="password"
        )
        
    with col_pass2:
        confirm_password = st.text_input(
            "Xác nhận mật khẩu *", 
            placeholder="Nhập lại mật khẩu",
            type="password"
        )
    
    st.markdown("### 📞 THÔNG TIN LIÊN HỆ (tùy chọn)")
    diachi = st.text_input("Địa chỉ", placeholder="123 Đường XYZ, Quận 1, TP.HCM")

    if st.button("🎯 TẠO MÃ QR", type="primary"):
        # Kiểm tra thông tin bắt buộc
        missing_fields = []
        
        if loai_doituong == "🚗 XE CÁ NHÂN HỌC SINH":
            if not hoten_hocsinh: missing_fields.append("Họ tên học sinh")
            if not ngaysinh_hocsinh: missing_fields.append("Ngày sinh học sinh")
            
        elif loai_doituong == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
            if not hoten_hocsinh: missing_fields.append("Họ tên học sinh")
            if not ngaysinh_hocsinh: missing_fields.append("Ngày sinh học sinh")
            if not hoten_chuxe: missing_fields.append("Họ tên chủ xe")
            if not ngaysinh_chuxe: missing_fields.append("Ngày sinh chủ xe")
            if not sdt_chuxe: missing_fields.append("Số điện thoại chủ xe")
            
        else:  # XE GIA ĐÌNH
            if not hoten_chuxe: missing_fields.append("Họ tên chủ xe")
            if not ngaysinh_chuxe: missing_fields.append("Ngày sinh chủ xe")
            if not sdt_chuxe: missing_fields.append("Số điện thoại chủ xe")
        
        if not bienso_xe: missing_fields.append("Biển số xe")
        if not custom_password: missing_fields.append("Mật khẩu tùy chỉnh")
        if not confirm_password: missing_fields.append("Xác nhận mật khẩu")
        
        if custom_password != confirm_password:
            st.error("⚠️ MẬT KHẨU XÁC NHẬN KHÔNG KHỚP!")
        elif missing_fields:
            st.error(f"⚠️ Vui lòng nhập các thông tin bắt buộc: {', '.join(missing_fields)}")
        else:
            # Tạo dictionary chứa thông tin
            fields = {
                "loai_xe": loai_doituong,
                "bienso_xe": bienso_xe,
                "diachi": diachi,
                "thoigian_taoma": "2025-01-01 00:00:00"
            }
            
            # Thêm thông tin theo loại xe
            if loai_doituong == "🚗 XE CÁ NHÂN HỌC SINH":
                fields.update({
                    "hoten_hocsinh": hoten_hocsinh,
                    "ngaysinh_hocsinh": ngaysinh_hocsinh,
                    "lop": lop,
                    "truong": truong,
                    "loai_xe_chi_tiet": loai_xe,
                    "mau_xe": mau_xe
                })
                ngaysinh_mo_qr = ngaysinh_hocsinh
                
            elif loai_doituong == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
                fields.update({
                    "hoten_hocsinh": hoten_hocsinh,
                    "ngaysinh_hocsinh": ngaysinh_hocsinh,
                    "lop": lop,
                    "truong": truong,
                    "hoten_chuxe": hoten_chuxe,
                    "ngaysinh_chuxe": ngaysinh_chuxe,
                    "sdt_chuxe": sdt_chuxe,
                    "quanhe_voihocsinh": quanhe_voihocsinh
                })
                ngaysinh_mo_qr = ngaysinh_hocsinh
                
            else:  # XE GIA ĐÌNH
                fields.update({
                    "hoten_chuxe": hoten_chuxe,
                    "ngaysinh_chuxe": ngaysinh_chuxe,
                    "sdt_chuxe": sdt_chuxe,
                    "loai_xe_chi_tiet": loai_xe,
                    "mau_xe": mau_xe
                })
                ngaysinh_mo_qr = ngaysinh_chuxe
            
            # Loại bỏ các trường rỗng
            fields = {k: v for k, v in fields.items() if v}
            
            data_json = json.dumps(fields, ensure_ascii=False)

            # Mã hóa 3 lớp với các mật khẩu khác nhau
            encrypted_default = encrypt_data(data_json, DEFAULT_PASSWORD)
            encrypted_birthdate = encrypt_data(data_json, ngaysinh_mo_qr)
            encrypted_custom = encrypt_data(data_json, custom_password)

            # Gộp cả ba vào một JSON
            combo_data = json.dumps({
                "cong_an": encrypted_default,
                "ngay_sinh": encrypted_birthdate,
                "custom": encrypted_custom
            }, ensure_ascii=False)

            # TẠO QR CODE - CÁCH MỚI ĐÃ SỬA LỖI
            qr_img = create_stable_qr_code(combo_data)
            
            # Tạo buffer cho hiển thị
            display_buf = BytesIO()
            qr_img.save(display_buf, format="PNG")
            display_buf.seek(0)
            
            # Tạo buffer RIÊNG cho download
            download_buf = BytesIO()
            qr_img.save(download_buf, format="PNG")
            download_buf.seek(0)
            
            # Hiển thị kết quả
            col_success1, col_success2 = st.columns(2)
            
            with col_success1:
                st.image(display_buf.getvalue(), caption="✅ MÃ QR ĐÃ TẠO", use_column_width=True)
                
                st.download_button(
                    "⬇️ TẢI MÃ QR VỀ MÁY",
                    download_buf.getvalue(), 
                    f"QR_{bienso_xe.replace(' ', '_')}.png",
                    "image/png"
                )
            
            with col_success2:
                st.success("🎉 TẠO MÃ QR THÀNH CÔNG!")
                
                # Hiển thị dữ liệu QR để copy
                st.markdown("### 📋 DỮ LIỆU QR ĐỂ SAO CHÉP:")
                st.code(combo_data, language="json")
                st.info("💡 **SAO CHÉP ĐOẠN CODE TRÊN để dán vào phần giải mã**")
                
                if loai_doituong == "🚗 XE CÁ NHÂN HỌC SINH":
                    st.info(f"**Loại:** Xe cá nhân học sinh")
                    st.info(f"**Học sinh:** {hoten_hocsinh}")
                    st.info(f"**Biển số:** {bienso_xe}")
                    
                elif loai_doituong == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
                    st.info(f"**Loại:** Xe gia đình - học sinh sử dụng tạm")
                    st.info(f"**Học sinh:** {hoten_hocsinh}")
                    st.info(f"**Chủ xe:** {hoten_chuxe} ({quanhe_voihocsinh})")
                    st.info(f"**Biển số:** {bienso_xe}")
                    
                else:
                    st.info(f"**Loại:** Xe gia đình")
                    st.info(f"**Chủ xe:** {hoten_chuxe}")
                    st.info(f"**Biển số:** {bienso_xe}")
                
                st.markdown("---")
                st.markdown("### 🔑 THÔNG TIN MẬT KHẨU:")
                st.success(f"**Mật khẩu tùy chỉnh:** {custom_password}")
                st.info(f"**Ngày sinh để mở QR:** {ngaysinh_mo_qr}")
                st.info("**Mật khẩu Công an:** Hệ thống")

# ---------- TAB 2: GIẢI MÃ THÔNG TIN ----------
with tab2:
    st.subheader("🔍 QUÉT MÃ QR ĐỂ TRA CỨU THÔNG TIN")
    
    st.markdown("### 📤 TẢI LÊN ẢNH CHỨA MÃ QR")
    uploaded = st.file_uploader("Chọn file ảnh", type=["png", "jpg", "jpeg"])
    
    st.markdown("---")
    st.markdown("### 📋 HOẶC NHẬP DỮ LIỆU QR THỦ CÔNG")
    manual_qr_data = st.text_area("Dán dữ liệu từ mã QR vào đây", 
                                 placeholder='{"cong_an": "encrypted_data...", "ngay_sinh": "encrypted_data...", "custom": "encrypted_data..."}', 
                                 height=150)
    
    st.markdown("---")
    st.markdown("### 🔑 CHỌN PHƯƠNG THỨC MỞ KHÓA")
    
    option = st.radio(
        "Chọn cách mở QR:",
        [
            "🔐 MẬT KHẨU TÙY CHỈNH", 
            "🎂 NGÀY SINH",
            "👮 MẬT KHẨU CÔNG AN"
        ],
        index=0
    )
    
    password_dec = ""
    password_field_key = ""
    
    if option == "🔐 MẬT KHẨU TÙY CHỈNH":
        password_dec = st.text_input("🔒 NHẬP MẬT KHẨU TÙY CHỈNH", 
                                   placeholder="Nhập mật khẩu bạn đã đặt khi tạo QR",
                                   type="password")
        password_field_key = "custom"
        st.info("💡 Nhập mật khẩu tùy chỉnh đã đặt khi tạo mã QR")
        
    elif option == "🎂 NGÀY SINH":
        password_dec = st.text_input("🔒 NHẬP NGÀY SINH", 
                                   placeholder="Nhập ngày sinh học sinh/chủ xe",
                                   help="Định dạng: dd/mm/yyyy hoặc dd-mm-yyyy")
        password_field_key = "ngay_sinh"
        st.info("💡 Nhập ngày sinh của học sinh (xe cá nhân) hoặc chủ xe (xe gia đình)")
        
    elif option == "👮 MẬT KHẨU CÔNG AN":
        password_dec = st.text_input("🔒 NHẬP MẬT KHẨU HỆ THỐNG", 
                                   type="password")
        password_field_key = "cong_an"
        st.info("💡 Nhập mật khẩu được cấp cho Công an")

    if st.button("🚀 GIẢI MÃ THÔNG TIN", type="primary"):
        if not password_dec:
            st.warning("⚠️ VUI LÒNG NHẬP MẬT KHẨU!")
            st.stop()
            
        encrypted_combo = None
        
        # Ưu tiên dữ liệu nhập thủ công
        if manual_qr_data and manual_qr_data.strip():
            try:
                encrypted_combo = manual_qr_data.strip()
                st.success("✅ ĐÃ NHẬN DỮ LIỆU QR THỦ CÔNG")
            except:
                st.error("❌ DỮ LIỆU QR KHÔNG HỢP LỆ!")
        
        # Nếu không có dữ liệu thủ công, thử đọc từ ảnh
        elif uploaded:
            try:
                image = Image.open(uploaded)
                st.image(image, caption="Ảnh đã tải lên", width=300)
                
                try:
                    from pyzbar.pyzbar import decode
                    import cv2
                    import numpy as np
                    
                    img_array = np.array(image)
                    if len(img_array.shape) == 3:
                        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    else:
                        img_cv = img_array
                        
                    qr_codes = decode(img_cv)
                    if qr_codes:
                        encrypted_combo = qr_codes[0].data.decode()
                        st.success("✅ ĐÃ ĐỌC THÀNH CÔNG MÃ QR TỪ ẢNH!")
                    else:
                        st.warning("⚠️ KHÔNG TÌM THẤY MÃ QR TRONG ẢNH. Vui lòng nhập thủ công.")
                        st.stop()
                except ImportError:
                    st.warning("⚠️ KHÔNG THỂ ĐỌC MÃ QR TỰ ĐỘNG. Vui lòng nhập thủ công dữ liệu QR ở trên.")
                    st.stop()
                    
            except Exception as e:
                st.error(f"❌ LỖI KHI XỬ LÝ ẢNH: {str(e)}")
                st.stop()
        else:
            st.warning("⚠️ VUI LÒNG TẢI LÊN ẢNH HOẶC NHẬP DỮ LIỆU QR!")
            st.stop()

        # Xử lý giải mã
        if encrypted_combo:
            try:
                combo_json = json.loads(encrypted_combo)
            except Exception:
                st.error("❌ DỮ LIỆU MÃ QR KHÔNG HỢP LỆ!")
                st.stop()

            decrypted = None
            used_method = ""
            
            try:
                decrypted = decrypt_data(combo_json[password_field_key], password_dec)
                
                if option == "🔐 MẬT KHẨU TÙY CHỈNH":
                    used_method = "MẬT KHẨU TÙY CHỈNH"
                elif option == "🎂 NGÀY SINH":
                    used_method = "NGÀY SINH"
                elif option == "👮 MẬT KHẨU CÔNG AN":
                    if password_dec == DEFAULT_PASSWORD:
                        used_method = "MẬT KHẨU CÔNG AN"
                    else:
                        used_method = "MẬT KHẨU HỆ THỐNG"
                        
            except Exception:
                st.error("❌ MẬT KHẨU KHÔNG CHÍNH XÁC!")
                st.stop()

            if decrypted:
                st.success(f"✅ GIẢI MÃ THÀNH CÔNG! ({used_method})")
                st.balloons()
                
                data = json.loads(decrypted)
                
                # Hiển thị thông tin theo loại xe
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("### 📊 THÔNG TIN CHUNG")
                    st.write(f"**Loại xe:** {data.get('loai_xe', 'N/A')}")
                    st.write(f"**Biển số:** {data.get('bienso_xe', 'N/A')}")
                    st.write(f"**Địa chỉ:** {data.get('diachi', 'N/A')}")
                    st.write(f"**Thời gian tạo:** {data.get('thoigian_taoma', 'N/A')}")
                
                with col_info2:
                    if data.get('loai_xe') == "🚗 XE CÁ NHÂN HỌC SINH":
                        st.markdown("### 👤 THÔNG TIN HỌC SINH")
                        st.write(f"**Họ tên:** {data.get('hoten_hocsinh', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh_hocsinh', 'N/A')}")
                        st.write(f"**Trường:** {data.get('truong', 'N/A')}")
                        st.write(f"**Lớp:** {data.get('lop', 'N/A')}")
                        if data.get('loai_xe_chi_tiet'):
                            st.write(f"**Loại xe:** {data.get('loai_xe_chi_tiet', 'N/A')}")
                        if data.get('mau_xe'):
                            st.write(f"**Màu xe:** {data.get('mau_xe', 'N/A')}")
                        
                    elif data.get('loai_xe') == "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM":
                        st.markdown("### 👤 THÔNG TIN HỌC SINH")
                        st.write(f"**Họ tên:** {data.get('hoten_hocsinh', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh_hocsinh', 'N/A')}")
                        st.write(f"**Trường:** {data.get('truong', 'N/A')}")
                        st.write(f"**Lớp:** {data.get('lop', 'N/A')}")
                        st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
                        st.write(f"**Chủ xe:** {data.get('hoten_chuxe', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh_chuxe', 'N/A')}")
                        st.write(f"**Quan hệ:** {data.get('quanhe_voihocsinh', 'N/A')}")
                        st.write(f"**Điện thoại:** {data.get('sdt_chuxe', 'N/A')}")
                        
                    else:  # XE GIA ĐÌNH
                        st.markdown("### 👨‍👩‍👧‍👦 THÔNG TIN CHỦ XE")
                        st.write(f"**Chủ xe:** {data.get('hoten_chuxe', 'N/A')}")
                        st.write(f"**Ngày sinh:** {data.get('ngaysinh_chuxe', 'N/A')}")
                        st.write(f"**Điện thoại:** {data.get('sdt_chuxe', 'N/A')}")
                        if data.get('loai_xe_chi_tiet'):
                            st.write(f"**Loại xe:** {data.get('loai_xe_chi_tiet', 'N/A')}")
                        if data.get('mau_xe'):
                            st.write(f"**Màu xe:** {data.get('mau_xe', 'N/A')}")
                
                # Chức năng cho Công an
                if option == "👮 MẬT KHẨU CÔNG AN":
                    st.markdown("---")
                    st.warning("🚨 CHỨC NĂNG BÁO CÁO VI PHẠM")
                    col_report1, col_report2 = st.columns(2)
                    
                    with col_report1:
                        if st.button("📧 GỬI THÔNG BÁO"):
                            if data.get('loai_xe') in ["🚗 XE CÁ NHÂN HỌC SINH", "🔄 XE GIA ĐÌNH - HỌC SINH SỬ DỤNG TẠM"]:
                                st.success(f"Đã gửi thông báo đến phụ huynh học sinh {data.get('hoten_hocsinh', '')}!")
                            else:
                                st.success(f"Đã gửi thông báo đến chủ xe {data.get('hoten_chuxe', '')}!")
                    
                    with col_report2:
                        if st.button("🏫 BÁO CÁO NHÀ TRƯỜNG"):
                            if data.get('truong'):
                                st.success(f"Đã báo cáo với trường {data.get('truong')}!")
                            else:
                                st.success("Đã ghi nhận vi phạm vào hệ thống!")

# ====== FOOTER ======
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎓 <strong>HỆ THỐNG QUẢN LÝ HỌC SINH THAM GIA GIAO THÔNG</strong></p>
    <p>Bản quyền © 2025 - Phát triển cho Cuộc thi Sáng kiến An toàn Giao thông</p>
</div>
""", unsafe_allow_html=True)
