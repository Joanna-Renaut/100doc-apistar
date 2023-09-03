import json
from typing import List
from apistar import App, Route, types, validators
from apistar.http import JSONResponse
from random import randint
# helpers


def load_health_data():
    with open('data/mock_health.json') as f:
        health_records = json.loads(f.read())
        # print(health_records)
        return {patient['nhs_num']: patient for patient in health_records}


health_records = load_health_data()
# health_records['nhs_num'] = int(health_records['nhs_num'])
VALID_ICD10 = set([diagnosis['icd10_diag_code'] for diagnosis in health_records.values()])
PATIENT_NOT_FOUND = 'Patient not found'


class Patient(types.Type):
    nhs_num = validators.String(allow_null=True)
    icd10_diag_code = validators.String(enum=list(VALID_ICD10))
    icd10_diag_desc = validators.String(max_length=300)
    generic_drug_name = validators.String()
    drug_company = validators.String(max_length=150)


def generate_random_nhs_num():
    return str(randint(0000000000, 9999999999))


def nhs_num_exists(nhs_num, health_records):
    return any(record['nhs_num'] == nhs_num for record in health_records.values())


def generate_unique_nhs_num(health_records, max_attempts=1000):
    for _ in range(max_attempts):
        nhs_num = generate_random_nhs_num()
        if not nhs_num_exists(nhs_num, health_records):
            nhs_num = generate_random_nhs_num()
            return nhs_num
    raise ValueError('Failed to generate a unique NHS number after multiple attempts')


# API methods
def list_patients() -> List[Patient]:
    return [Patient(patient[1]) for patient in health_records.items()]
    # print(patients)
    # return patients


def create_patient(patient: Patient):
    nhs_num = patient.nhs_num if patient.nhs_num else generate_unique_nhs_num(health_records)
    patient_data = dict(patient)
    patient_data['nhs_num'] = nhs_num
    health_records[nhs_num] = patient_data

    return JSONResponse(patient_data, status_code=201)


def get_patient(nhs_num) -> JSONResponse:
    patient = health_records.get(nhs_num)
    if not patient:
        error = {'error': PATIENT_NOT_FOUND}
        return JSONResponse(error, status_code=404)
    return JSONResponse(Patient(patient), status_code=200)


def update_patient(nhs_num, patient: Patient) -> JSONResponse:
    if not health_records.get(nhs_num):
        error = {'error': PATIENT_NOT_FOUND}
        return JSONResponse(error, status_code=404)
    updated_patient_data = dict(patient)
    updated_patient_data['nhs_num'] = nhs_num
    health_records[nhs_num] = updated_patient_data

    return JSONResponse(updated_patient_data, status_code=200)


def delete_patient(nhs_num) -> JSONResponse:
    if not health_records.get(nhs_num):
        error = {'error': PATIENT_NOT_FOUND}
        return JSONResponse(error, status_code=404)
    del health_records[nhs_num]
    print('deleted')
    return JSONResponse(content='Deleted successfully', status_code=204)


routes = [
    Route('/', method='GET', handler=list_patients),
    Route('/', method='POST', handler=create_patient),
    Route('/{nhs_num}/', method='GET', handler=get_patient),
    Route('/{nhs_num}/', method='PUT', handler=update_patient),
    Route('/{nhs_num}/', method='DELETE', handler=delete_patient)
]

app = App(routes=routes)

if __name__ == '__main__':
    app.serve('127.0.0.1', 5000, debug=True)