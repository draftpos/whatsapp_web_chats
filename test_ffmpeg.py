import subprocess
import os

ffmpeg_exe = 'ffmpeg'
# Create a dummy silent webm file
try:
    subprocess.run([ffmpeg_exe, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', '1', '-c:a', 'libopus', 'test_in.webm'], check=True, capture_output=True)
    print("Created test_in.webm")
except Exception as e:
    print(f"Failed to create test_in.webm: {e}")

try:
    res = subprocess.run([
        ffmpeg_exe, '-y', '-i', 'test_in.webm',
        '-vn', '-c:a', 'libopus', '-b:a', '32k',
        '-ar', '16000', '-ac', '1',
        'test_out.ogg'
    ], check=True, capture_output=True, text=True)
    print("Successfully converted to libopus Ogg!")
    print(res.stdout)
    print(res.stderr)
except subprocess.CalledProcessError as e:
    print("Failed to convert with libopus:")
    print(e.stderr)
    
    try:
        res = subprocess.run([
            ffmpeg_exe, '-y', '-i', 'test_in.webm',
            '-vn', '-c:a', 'opus', '-strict', '-2', '-b:a', '32k',
            '-ar', '16000', '-ac', '1',
            'test_out.ogg'
        ], check=True, capture_output=True, text=True)
        print("Successfully converted with native opus Ogg!")
    except subprocess.CalledProcessError as e2:
        print("Failed to convert with native opus:")
        print(e2.stderr)
