
try:
    import shutil
    print("shutil imported")
    import pydub
    print("pydub imported")
    import imageio_ffmpeg
    print("imageio_ffmpeg imported")
    import aliyunsdkcore
    print("aliyunsdkcore imported")
    from app.services.media.asr import aliyun_asr_service
    print("aliyun_asr_service imported")
except Exception as e:
    print(f"Error: {e}")
