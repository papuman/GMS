#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Hacienda API Test

This script directly tests the Hacienda sandbox API to verify credentials
and endpoints without going through Odoo models.
"""

import requests
import base64
import json
from datetime import datetime

# Hacienda sandbox credentials
HACIENDA_USERNAME = 'cpf-01-1313-0574@stag.comprobanteselectronicos.go.cr'
HACIENDA_PASSWORD = 'e8KLJRHzRA1P0W2ybJ5T'

# Sandbox API URL
SANDBOX_URL = 'https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1'


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_result(success, message):
    """Print a result with status indicator."""
    status = "✅" if success else "❌"
    print(f"{status} {message}")


def test_authentication():
    """Test basic authentication against Hacienda sandbox API."""

    print_header("Test 1: Basic Authentication")

    # Create Basic Auth header
    credentials = f"{HACIENDA_USERNAME}:{HACIENDA_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json',
    }

    print(f"Testing credentials:")
    print(f"  Username: {HACIENDA_USERNAME}")
    print(f"  Sandbox URL: {SANDBOX_URL}")

    # Test 1: Try a simple GET to a non-existent resource (should get 404, not 401)
    try:
        url = f"{SANDBOX_URL}/recepcion/test"
        print(f"\n  Testing endpoint: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        print(f"  Response Status: {response.status_code}")
        print(f"  Response Text: {response.text[:200]}")

        if response.status_code == 401:
            print_result(False, "Authentication failed - Invalid credentials")
            return False
        elif response.status_code == 403:
            print_result(False, "Forbidden - Authorization issue")
            print(f"  Response: {response.text}")
            return False
        elif response.status_code == 404:
            print_result(True, "Authentication successful (404 = endpoint doesn't exist but auth worked)")
            return True
        else:
            print_result(True, f"Unexpected status {response.status_code} but not auth error")
            return True

    except requests.exceptions.Timeout:
        print_result(False, "Connection timeout")
        return False
    except requests.exceptions.ConnectionError as e:
        print_result(False, f"Connection error: {str(e)}")
        return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


def test_check_status():
    """Test checking status of a document."""

    print_header("Test 2: Check Document Status (Query)")

    credentials = f"{HACIENDA_USERNAME}:{HACIENDA_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json',
    }

    # Use a sample clave (this will likely return 404, which is fine)
    test_clave = '50601051281225040031012345670010000000171976631921'

    url = f"{SANDBOX_URL}/recepcion/{test_clave}"
    print(f"  Querying clave: {test_clave}")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)

        print(f"  Response Status: {response.status_code}")
        print(f"  Response Text: {response.text[:500]}")

        if response.status_code == 401:
            print_result(False, "Authentication failed")
            return False
        elif response.status_code == 403:
            print_result(False, "Forbidden - Authorization issue")
            return False
        elif response.status_code == 404:
            print_result(True, "Document not found (expected for test clave)")
            return True
        elif response.status_code == 200:
            print_result(True, "Document found - parsing response")
            try:
                data = response.json()
                print(f"  Estado: {data.get('ind-estado', 'N/A')}")
            except:
                pass
            return True
        else:
            print_result(True, f"Received response (status {response.status_code})")
            return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


def test_submit_document():
    """Test submitting a document (with dummy data)."""

    print_header("Test 3: Submit Document (Dry Run)")

    credentials = f"{HACIENDA_USERNAME}:{HACIENDA_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json',
    }

    # Create a minimal test payload
    test_clave = '50601051281225040031012345670010000000991234567890'
    test_xml = '<FacturaElectronica>Test</FacturaElectronica>'
    xml_base64 = base64.b64encode(test_xml.encode('utf-8')).decode('utf-8')

    payload = {
        'clave': test_clave,
        'fecha': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-06:00'),
        'emisor': {
            'tipoIdentificacion': '01',
            'numeroIdentificacion': '113130574',
        },
        'receptor': {
            'tipoIdentificacion': '05',
            'numeroIdentificacion': '000000000000',
        },
        'comprobanteXml': xml_base64,
    }

    url = f"{SANDBOX_URL}/recepcion"
    print(f"  Submitting to: {url}")
    print(f"  Test Clave: {test_clave}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"  Response Status: {response.status_code}")
        print(f"  Response Text: {response.text[:500]}")

        if response.status_code == 401:
            print_result(False, "Authentication failed")
            return False
        elif response.status_code == 403:
            print_result(False, "Forbidden - Authorization issue")
            return False
        elif response.status_code == 400:
            print_result(True, "Validation error (expected for dummy data)")
            return True
        elif response.status_code in [200, 201]:
            print_result(True, "Document accepted!")
            try:
                data = response.json()
                print(f"  Estado: {data.get('ind-estado', 'N/A')}")
            except:
                pass
            return True
        else:
            print_result(True, f"Received response (status {response.status_code})")
            return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


def main():
    """Run all API tests."""

    print_header("Hacienda Sandbox API Direct Testing")

    results = []

    # Test 1: Authentication
    results.append(("Authentication", test_authentication()))

    # Test 2: Check status
    results.append(("Check Status", test_check_status()))

    # Test 3: Submit document
    results.append(("Submit Document", test_submit_document()))

    # Summary
    print_header("Test Summary")

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)

    for test_name, result in results:
        print_result(result, test_name)

    print(f"\nPassed: {passed_tests}/{total_tests}")

    if passed_tests == total_tests:
        print("\n✅ All API tests passed - Hacienda sandbox is accessible!")
    else:
        print("\n⚠️  Some tests failed - check credentials or API configuration")


if __name__ == '__main__':
    main()
