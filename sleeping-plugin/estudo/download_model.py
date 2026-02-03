import urllib.request
import os

model_url = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
model_path = 'face_landmarker.task'

print(f'Baixando modelo para: {os.path.abspath(model_path)}')
urllib.request.urlretrieve(model_url, model_path)
print('Download concluído!')
