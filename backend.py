import io
import uuid
import streamlit as st
from supabase import create_client, Client
from PIL import Image

# Initialize Supabase client
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def compress_image(uploaded_file):
    """
    Compresses an uploaded image:
    - Downscales so the longest edge is max 1200px
    - Converts to JPEG format at 75% quality
    """
    img = Image.open(uploaded_file)
    
    # Handle EXIF orientation (optional but good for mobile photos)
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Convert to RGB if it's RGBA or P
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    MAX_SIZE = (1200, 1200)
    img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=75)
    output.seek(0)
    return output.read()

def upload_photo(van_id: str, index: int, image_bytes: bytes) -> str:
    """
    Uploads a photo to Supabase storage and returns the public URL.
    """
    import time
    supabase = get_supabase()
    timestamp = int(time.time())
    file_path = f"{van_id}/{timestamp}_photo_{index}.jpg"
    
    try:
        res = supabase.storage.from_("van-photos").upload(
            file_path,
            image_bytes,
            {"content-type": "image/jpeg"}
        )
        url = supabase.storage.from_("van-photos").get_public_url(file_path)
        return url
    except Exception as e:
        st.error(f"Failed to upload photo: {e}")
        return ""
