"""
Test de las funciones de utilidad
"""
from de_p3.processing import (
    surrogate_key,
    format_age,
    normalize_pixel_spacing,
    normalize_contrast_agent,
    dicom_to_jpeg
)
from pathlib import Path

print("="*60)
print("TESTING UTILITY FUNCTIONS")
print("="*60)

# Test 1: surrogate_key
print("\n1. Testing surrogate_key():")
values1 = {"name": "John", "age": 30}
values2 = {"age": 30, "name": "John"}  # Same values, different order
values3 = {"name": "Jane", "age": 30}  # Different values

key1 = surrogate_key(values1)
key2 = surrogate_key(values2)
key3 = surrogate_key(values3)

print(f"   Key 1: {key1}")
print(f"   Key 2: {key2}")
print(f"   Key 3: {key3}")
print(f"   ✅ Same values produce same key: {key1 == key2}")
print(f"   ✅ Different values produce different key: {key1 != key3}")

# Test 2: format_age
print("\n2. Testing format_age():")
test_ages = ['061Y', '045Y', '080Y', '', None, 'invalid', '25']
for age in test_ages:
    result = format_age(age)
    print(f"   format_age('{age}') = {result}")

# Test 3: normalize_pixel_spacing
print("\n3. Testing normalize_pixel_spacing():")
test_spacings = [0.62, 0.78, 0.59, 0.85, '0.72', None, 'invalid']
for spacing in test_spacings:
    result = normalize_pixel_spacing(spacing)
    print(f"   normalize_pixel_spacing({spacing}) = {result}")

# Test 4: normalize_contrast_agent
print("\n4. Testing normalize_contrast_agent():")
test_agents = ['CONTRAST AGENT APPLIED', 'NONE', '', None, 'X', ' ', 'Valid Agent Name']
for agent in test_agents:
    result = normalize_contrast_agent(agent)
    print(f"   normalize_contrast_agent('{agent}') = '{result}'")

# Test 5: dicom_to_jpeg
print("\n5. Testing dicom_to_jpeg():")
dicom_dir = Path("data/dicom_dir")
output_dir = Path("data/output/jpeg_images")

if dicom_dir.exists():
    # Convert first DICOM file
    dicom_files = list(dicom_dir.glob("*.dcm"))
    if dicom_files:
        test_file = dicom_files[0]
        print(f"   Converting: {test_file.name}")
        jpeg_path = dicom_to_jpeg(test_file, output_dir, size=(256, 256))
        print(f"   ✅ Saved to: {jpeg_path}")
        print(f"   ✅ File exists: {Path(jpeg_path).exists()}")
    else:
        print("   ⚠️ No DICOM files found")
else:
    print("   ⚠️ DICOM directory not found")

print("\n" + "="*60)
print("TESTS COMPLETED")
print("="*60)
