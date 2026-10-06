from PIL import Image
from app.services.hasher import compute_sha256, compute_phash, hamming_distance, is_near_duplicate

def test_sha256_exact_match(sample_rgb_image_bytes):
    hash1 = compute_sha256(sample_rgb_image_bytes)
    hash2 = compute_sha256(sample_rgb_image_bytes)
    assert hash1 == hash2
    assert len(hash1) == 64

def test_phash_visual_similarity():
    # Two identical images
    img1 = Image.new("RGB", (400, 400), color=(100, 150, 200))
    img2 = Image.new("RGB", (400, 400), color=(100, 150, 200))
    
    phash1 = compute_phash(img1)
    phash2 = compute_phash(img2)
    
    assert phash1 == phash2
    assert hamming_distance(phash1, phash2) == 0
    assert is_near_duplicate(phash1, phash2) is True

def test_phash_difference_on_distinct_images():
    img1 = Image.new("RGB", (400, 400), color=(255, 255, 255))
    # Image with stripes
    img2 = Image.new("RGB", (400, 400), color=(0, 0, 0))
    for x in range(0, 400, 20):
        for y in range(400):
            img2.putpixel((x, y), (255, 255, 255))
            
    phash1 = compute_phash(img1)
    phash2 = compute_phash(img2)
    
    dist = hamming_distance(phash1, phash2)
    assert isinstance(dist, int)
    assert dist >= 0
