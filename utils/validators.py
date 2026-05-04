from datetime import datetime
import re

def validate_rsa_id(id_number):
    """
    Validate South African ID number (13 digits)
    Format: YYMMDD SSSS C A
    - YYMMDD: Date of birth
    - SSSS: Gender (Female 0000-4999, Male 5000-9999)
    - C: Citizenship (0=SA citizen, 1=Permanent resident)
    - A: Checksum (8 or 9 usually)
    """
    if not id_number or not isinstance(id_number, str):
        return False, "ID number is required"
    
    # Remove any spaces
    id_number = id_number.strip()
    
    # Check length
    if len(id_number) != 13:
        return False, "ID number must be exactly 13 digits"
    
    # Check if all digits
    if not id_number.isdigit():
        return False, "ID number must contain only digits"
    
    # Extract date of birth
    try:
        year = int(id_number[0:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])
        
        # Adjust year (assuming 2000+ for simplicity)
        full_year = 2000 + year if year < 50 else 1900 + year
        
        date_of_birth = datetime(full_year, month, day)
        
        # Check if date is valid
        if date_of_birth > datetime.now():
            return False, "Invalid date of birth (future date)"
        
        return True, date_of_birth
    except ValueError:
        return False, "Invalid date format in ID number"

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    today = datetime.now()
    age = today.year - date_of_birth.year
    if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
        age -= 1
    return age

def validate_learner_age(age):
    """Validate learner age between 6 and 12"""
    if age < 6:
        return False, "Learner must be at least 6 years old"
    if age > 12:
        return False, "Learner must not exceed 12 years old"
    return True, "Valid age"

def determine_grade_from_age(age):
    """Determine appropriate grade based on age"""
    # Age 6 = Grade 1, Age 7 = Grade 2, etc.
    grade = age - 5
    if grade < 1:
        grade = 1
    if grade > 7:
        grade = 7
    return grade