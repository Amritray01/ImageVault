import hashlib
import math
from PIL import Image

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def compute_phash(img: Image.Image) -> str:
    img_gray = img.convert("L").resize((32, 32), Image.Resampling.BILINEAR)
    pixels = list(img_gray.get_flattened_data()) if hasattr(img_gray, "get_flattened_data") else list(img_gray.getdata())
    
    matrix = [pixels[i * 32:(i + 1) * 32] for i in range(32)]
    N = 32
    dct_matrix = [[0.0] * N for _ in range(N)]
    cos_factors = [[math.cos(((2 * x + 1) * u * math.pi) / (2 * N)) for x in range(N)] for u in range(N)]
    
    for u in range(8):
        c_u = 1.0 / math.sqrt(2.0) if u == 0 else 1.0
        for v in range(8):
            c_v = 1.0 / math.sqrt(2.0) if v == 0 else 1.0
            total = sum(matrix[x][y] * cos_factors[u][x] * cos_factors[v][y] for x in range(N) for y in range(N))
            dct_matrix[u][v] = 0.25 * (2.0 / N) * c_u * c_v * total

    coefficients = [dct_matrix[u][v] for u in range(8) for v in range(8) if not (u == 0 and v == 0)]
    median = sorted(coefficients)[len(coefficients) // 2]
    
    bits = ["1" if dct_matrix[u][v] > median else "0" for u in range(8) for v in range(8)]
    return f"{int(''.join(bits), 2):016x}"

def hamming_distance(hash1: str, hash2: str) -> int:
    return (int(hash1, 16) ^ int(hash2, 16)).bit_count()

def is_near_duplicate(hash1: str, hash2: str, threshold: int = 6) -> bool:
    return hamming_distance(hash1, hash2) <= threshold
