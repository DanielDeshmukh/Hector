import httpx, os
from dotenv import load_dotenv
load_dotenv(r'D:\Vs Code\VS code\Hector\.env')
resp = httpx.post(
    os.getenv('NIM_BASE_URL') + '/embeddings',
    headers={'Authorization': f'Bearer {os.getenv("NIM_API_KEY")}', 'Content-Type': 'application/json'},
    json={'input': ['test'], 'model': 'nvidia/nv-embedqa-e5-v5', 'encoding_format': 'float', 'input_type': 'passage'},
    timeout=30,
)
data = resp.json()
print('Dim:', len(data['data'][0]['embedding']))
