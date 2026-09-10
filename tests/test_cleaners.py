"""Unit tests for individual data cleaning and normalization functions."""
import pytest
from src.cleaners import (
    clean_date_of_birth, clean_phone_number, clean_name_field,
    clean_gender, clean_zip_code, clean_mrn, clean_email
)

def test_clean_date_formats():
    assert clean_date_of_birth("1985-04-12") == "1985-04-12"
    assert clean_date_of_birth("04/12/1985") == "1985-04-12"
    assert clean_date_of_birth("25/04/1985") == "1985-04-25"
    assert clean_date_of_birth("1985/04/12") == "1985-04-12"
    assert clean_date_of_birth("invalid-date") is None
    assert clean_date_of_birth("1990-13-45") is None
    assert clean_date_of_birth("") is None

def test_clean_phone_number():
    assert clean_phone_number("(555) 123-4567") == "+1-555-123-4567"
    assert clean_phone_number("555.123.4567") == "+1-555-123-4567"
    assert clean_phone_number("1-555-123-4567") == "+1-555-123-4567"
    assert clean_phone_number("5551234567") == "+1-555-123-4567"
    assert clean_phone_number("Invalid") is None
    assert clean_phone_number("123") is None

def test_clean_name_field():
    assert clean_name_field("Dr. Robert Smith MD") == "Robert Smith"
    assert clean_name_field("mr. john doe jr.") == "John Doe"
    assert clean_name_field("  MARY   JANE  ") == "Mary Jane"
    assert clean_name_field("Sarah Connor, PhD") == "Sarah Connor"

def test_clean_gender():
    assert clean_gender("Male") == "M"
    assert clean_gender("MALE") == "M"
    assert clean_gender("man") == "M"
    assert clean_gender("Female") == "F"
    assert clean_gender("woman") == "F"
    assert clean_gender("Non-Binary") == "O"
    assert clean_gender("unknown") == "U"
    assert clean_gender(None) == "U"

def test_clean_zip_code():
    assert clean_zip_code("90210") == "90210"
    assert clean_zip_code("90210-1234") == "90210-1234"
    assert clean_zip_code("902101234") == "90210-1234"
    assert clean_zip_code("abc") is None

def test_clean_mrn():
    assert clean_mrn("MRN-1234567") == "MRN-1234567"
    assert clean_mrn("1234567") == "MRN-1234567"
    assert clean_mrn("0000000") is None
    assert clean_mrn("") is None

def test_clean_email():
    assert clean_email("John.Doe@Hospital.org") == "john.doe@hospital.org"
    assert clean_email("invalid-email-address") is None
