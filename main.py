from fastapi import FastAPI, Path, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

class Patient(BaseModel):

    id: Annotated[str, Field(..., description="Unique identifier for the patient", example="P001")] 
    name: Annotated[str, Field(..., description="Full name of the patient", example="John Doe")]
    city: Annotated[str, Field(..., description="City of residence", example="New York")] 
    age: Annotated[int, Field(..., gt=0, lt=120, description="Age of the patient in years", example=30)]
    gender: Annotated[Literal["Male", "Female", "Other"], Field(..., description="Gender of the patient", example="Male")]      
    height: Annotated[float, Field(..., gt=0, description="Height of the patient in centimeters", example=175.0)]
    weight: Annotated[float, Field(..., gt=0, description="Weight of the patient in kilograms", example=70.0)]
    
    @computed_field
    @property
    def bmi(self) -> float:
        height_in_meters = self.height / 100
        return round(self.weight / (height_in_meters ** 2), 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        bmi_value = self.bmi
        if bmi_value < 18.5:
            return "Underweight"
        elif 18.5 <= bmi_value < 25:
            return "Normal"
        elif 25 <= bmi_value < 30:
            return "Obese"


class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field( default=None, description="Full name of the patient", example="John Doe")]
    city: Annotated[Optional[str], Field(default=None, description="City of residence", example="New York")] 
    age: Annotated[Optional[int], Field(default=None, gt=0, lt=120, description="Age of the patient in years", example=30)]
    gender: Annotated[Optional[Literal["Male", "Female", "Other"]], Field(default=None, description="Gender of the patient", example="Male")]      
    height: Annotated[Optional[float], Field(default=None, gt=0, description="Height of the patient in centimeters", example=175.0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0, description="Weight of the patient in kilograms", example=70.0)]
    




def load_data():
    with open("patients.json", "r") as file:
        data = json.load(file)
    return data

def save_data(data):
    with open("patients.json", "w") as file:
        json.dump(data, file) 


@app.get("/")
def hello():
    return {"message": "Patient Management System"}


@app.get("/about")
def about():
    return {"message": "Fully functional patient management system built with FastAPI."}


@app.get("/view")
def view_patients():
    data = load_data()
    return data

@app.get("/view/{patient_id}")
def view_patient(patient_id: str = Path(..., description="The ID of the patient to retrieve", example="P001")):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")



@app.get("/sort")
def sort_patients(sort_by: str = Query(..., description="The field to sort patients by", example="bmi"), order: str = Query("asc", description="Sort order: 'asc' for ascending, 'desc' for descending", example="asc")):
    valid_fields = {"height", "weight", "bmi"}

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Valid fields are: {', '.join(valid_fields)}")
    
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid order. Use 'asc' or 'desc'.")
    
    data = load_data()
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=(order == "desc"))
    return sorted_data



@app.post("/create")
def create_patient(patient: Patient): 
    # load data
    data = load_data()

    # Check if patient ID already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient ID already exists.")
    
    # Add new patient
    data[patient.id] = patient.model_dump(exclude=['id']) 

    # Save data
    save_data(data)

    return JSONResponse(content={"message": "Patient created successfully."}, status_code=201)



@app.put("/update/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found.")
    
    existing_patient_data = data[patient_id]
    updated_data = patient_update.model_dump(exclude_unset=True)

    for key, value in updated_data.items():
        existing_patient_data[key] = value

    updated_patient = Patient(id=patient_id, **existing_patient_data)
    data[patient_id] = updated_patient.model_dump(exclude=['id'])

    save_data(data)

    return JSONResponse(content={"message": "Patient updated successfully."}, status_code=200)