from apistar import test
from app import app, health_records, PATIENT_NOT_FOUND, generate_unique_nhs_num
import random

client = test.TestClient(app)


def test_list_patients():
    response = client.get('/')
    assert response.status_code == 200

    json_rsp = response.json()
    patient_count = len(health_records)
    assert len(json_rsp) == patient_count

    first_record_nhs_num = list(health_records.keys())[0]
    expected = health_records[first_record_nhs_num]
    print(expected)
    print(json_rsp[0])
    assert json_rsp[0] == expected


def test_create_patient():
    patient_count = len(health_records)
    data = {
        'icd10_diag_code': 'C4310',
        'icd10_diag_desc': 'Test description',
        'generic_drug_name': 'Test drug',
        'drug_company': 'Test company'
    }
    response = client.post('/', data=data)
    assert response.status_code == 201
    assert len(health_records) == patient_count + 1

    created_patient = response.json()
    created_nhs_number = created_patient.get('nhs_num')

    response = client.get(f'/{created_nhs_number}')
    expected = {
        'nhs_num': created_nhs_number,
        'icd10_diag_code': 'C4310',
        'icd10_diag_desc': 'Test description',
        'generic_drug_name': 'Test drug',
        'drug_company': 'Test company'
    }
    assert response.json() == expected


def test_create_patient_after_delete():
    patient_count = len(health_records)

    # Get a patient's nhs_num from health_records
    nhs_num = list(health_records.keys())[0]

    # delete patient
    response = client.delete(f'/{nhs_num}/')
    assert response.status_code == 204
    assert len(health_records) == patient_count - 1

    # create another patient
    data = {
            'icd10_diag_code': 'C4310',
            'icd10_diag_desc': 'Test description',
            'generic_drug_name': 'Test drug',
            'drug_company': 'Test company'
        }
    response = client.post('/', data=data)
    assert response.status_code == 201
    assert len(health_records) == patient_count # patient count should be back to before the delete above


def test_create_patient_missing_fields():
    data = {'key': '6485082646'}
    response = client.post('/', data=data)
    assert response.status_code == 400

    errors = response.json()
    assert errors['icd10_diag_code'] == 'The ICD10 code is required.'
    assert errors['icd10_diag_desc'] == 'The ICD10 long description is required.'
    assert errors['generic_drug_name'] == 'The generic drug name being used for treatment is required.'
    assert errors['drug_company'] == 'The name of the drug company supplying the drug is required.'


def test_create_patient_field_validation():
    data = {
        'icd10_diag_code': 'feefifofum',
        'icd10_diag_desc': 'x'*302,
        'generic_drug_name': 'Test drug',
        'drug_company': 'x'*152
    }

    response = client.post('/', data=data)
    assert response.status_code == 400

    errors = response.json()
    assert 'Must be one of' in errors['icd10_diag_code']
    assert errors['icd10_diag_desc'] == 'Must have no more than 300 characters'
    assert errors['drug_company'] == 'Must have no more than 150 characters'


def test_get_patient():
    response = client.get('/1599991721/')
    assert response.status_code == 200

    expected = {
        'nhs_num': '1599991721',
        'icd10_diag_code':'S42153D',
        'icd10_diag_desc':'Displaced fracture of neck of scapula, unspecified shoulder, '
                          'subsequent encounter for fracture with routine healing',
        'generic_drug_name':'Miconazole Nitrate',
        'drug_company':'CDMA/Quality Choice'
    }
    assert response.json() == expected


def test_get_patient_not_found():
    nhs_num = generate_unique_nhs_num(health_records)
    response = client.get(f'/{nhs_num}')
    assert response.status_code == 404
    assert response.json() == {'error': PATIENT_NOT_FOUND}


def test_update_patient():
    data = {
        'icd10_diag_code': 'C4310',
        'icd10_diag_desc': 'Test description',
        'generic_drug_name': 'Test drug',
        'drug_company': 'Test company'
    }
    response = client.put('/7029883195/', data=data)
    assert response.status_code == 200

    expected = {
        'nhs_num': '7029883195',
        'icd10_diag_code': 'C4310',
        'icd10_diag_desc': 'Test description',
        'generic_drug_name': 'Test drug',
        'drug_company': 'Test company'
    }
    assert response.json() == expected

    response = client.get('/7029883195/')
    assert response.json() == expected


def test_update_patient_not_found():
    data = {
        'icd10_diag_code': 'C4310',
        'icd10_diag_desc': 'Test description',
        'generic_drug_name': 'Test drug',
        'drug_company': 'Test company'
    }

    nhs_num = generate_unique_nhs_num(health_records)
    response = client.put(f'/{nhs_num}', data=data)

    assert response.status_code == 404
    assert response.json() == {'error': PATIENT_NOT_FOUND}


def test_update_patient_validation():
    data = {
        'icd10_diag_code': 'feefifofum',
        'icd10_diag_desc': 'x' * 302,
        'generic_drug_name': 'Test drug',
        'drug_company': 'x' * 152
    }

    response = client.put('/6376797040/', data=data)
    assert response.status_code == 400

    errors = response.json()
    assert 'Must be one of' in errors['icd10_diag_code']
    assert errors['icd10_diag_desc'] == 'Must have no more than 300 characters'
    assert errors['drug_company'] == 'Must have no more than 150 characters'


def test_delete_patient():
    patient_count = len(health_records)

    # randomly select 3 nhs num from the dataset
    select_nhs_numbers = random.sample(list(health_records.keys()), 3)

    for nhs_num in select_nhs_numbers:
        response = client.delete(f'/{nhs_num}/')
        assert response.status_code == 204

        response = client.get(f'/{nhs_num}/')
        assert response.status_code == 404

    assert len(health_records) == patient_count - 3