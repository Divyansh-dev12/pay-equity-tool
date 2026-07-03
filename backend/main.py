from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import pandas as pd
import numpy as np
import io
import json
import math
from datetime import datetime

from analysis_regression import PayEquityRegressionAnalyzer
from analysis_median import run_median_analysis
from analytics import build_breakdowns
from insights import regression_insights, median_insights, median_recommendations
from chatbot import answer as chat_answer, teach as chat_teach, load_taught
from models import AnalysisRequest, ChatRequest, TeachRequest
from synthetic_data import generate_sample_dataset, generate_median_reference


def clean_dict(d):
    """Recursively convert NaN/inf and numpy types into JSON-safe values."""
    if isinstance(d, dict):
        return {k: clean_dict(v) for k, v in d.items()}
    if isinstance(d, list):
        return [clean_dict(x) for x in d]
    if isinstance(d, (float, np.floating)):
        f = float(d)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(d, (int, np.integer)):
        return int(d)
    if isinstance(d, (bool, np.bool_)):
        return bool(d)
    return d


def json_response(payload: dict) -> Response:
    return Response(content=json.dumps(clean_dict(payload)), media_type="application/json")


app = FastAPI(title="Pay Equity Analyzer", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _prep_employee_df(df: pd.DataFrame) -> pd.DataFrame:
    """Common cleaning. NOTE: job_level stays categorical ('L1','L2',...)."""
    required = ['employee_id', 'job_title', 'job_level', 'base_salary', 'gender']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400,
                            detail=f"Missing required columns: {', '.join(missing)}")
    df = df.copy()
    df['gender'] = df['gender'].astype(str).str.strip().str.title()
    df['base_salary'] = pd.to_numeric(df['base_salary'], errors='coerce')
    if 'location' not in df.columns:
        df['location'] = 'Unknown'
    if 'tenure_years' not in df.columns:
        df['tenure_years'] = None
    if 'performance_rating' not in df.columns:
        df['performance_rating'] = None
    if 'job_function' not in df.columns:
        df['job_function'] = df.get('job_title', 'General')
    return df


def _run_regression(df: pd.DataFrame) -> dict:
    analyzer = PayEquityRegressionAnalyzer(df)
    result = analyzer.run_full_analysis(outlier_sigma=3.0, underpaid_sigma=1.0)
    breakdowns = build_breakdowns(df)
    return {
        'method': 'regression',
        'model_summary': result.model_summary,
        'coefficients': result.coefficients,
        'predictions': result.predictions,
        'anomalies': result.anomalies,
        'recommendations': result.recommendations,
        'data_quality': result.data_quality,
        'model_stats': result.model_stats,
        'breakdowns': breakdowns,
        'insights': regression_insights(result.model_stats, result.recommendations,
                                        breakdowns, result.anomalies),
        'timestamp': datetime.now().isoformat(),
    }


# --------------------------------------------------------------------------- #
# Meta / sample data
# --------------------------------------------------------------------------- #
@app.get("/")
def read_root():
    return {"status": "online", "message": "Pay Equity Analyzer API", "version": "2.0.0"}


@app.get("/api/sample-data")
def get_sample_data():
    df = generate_sample_dataset()
    return json_response({
        "data": df.to_dict('records'),
        "columns": df.columns.tolist(),
        "rows": len(df),
        "note": "Synthetic Indian compensation dataset (fixed pay, INR)",
    })


@app.get("/api/sample-median")
def get_sample_median():
    mt = generate_median_reference()
    return json_response({
        "data": mt.to_dict('records'),
        "columns": mt.columns.tolist(),
        "rows": len(mt),
    })


# --------------------------------------------------------------------------- #
# Regression model
# --------------------------------------------------------------------------- #
@app.post("/api/analyze")
async def analyze_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        df = _prep_employee_df(df)
        return json_response(_run_regression(df))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/api/analyze-json")
async def analyze_json(request: AnalysisRequest):
    try:
        df = _prep_employee_df(pd.DataFrame(request.employees))
        return json_response(_run_regression(df))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------------------------------- #
# Linear (Median) model
# --------------------------------------------------------------------------- #
@app.post("/api/analyze-median")
async def analyze_median(request: AnalysisRequest):
    """JSON body: { employees: [...], median_table?: [...] }"""
    try:
        df = _prep_employee_df(pd.DataFrame(request.employees))
        median_df = None
        if request.median_table:
            median_df = pd.DataFrame(request.median_table)
        result = run_median_analysis(df, median_table=median_df)
        result['insights'] = median_insights(result)
        result['recommendations'] = median_recommendations(result)
        result['timestamp'] = datetime.now().isoformat()
        return json_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analyze-median-upload")
async def analyze_median_upload(file: UploadFile = File(...),
                                median_file: UploadFile = File(None)):
    """Employee CSV + optional median-benchmark CSV (job_function,job_level,median_salary)."""
    try:
        contents = await file.read()
        df = _prep_employee_df(pd.read_csv(io.StringIO(contents.decode('utf-8'))))
        median_df = None
        if median_file is not None:
            mcontents = await median_file.read()
            median_df = pd.read_csv(io.StringIO(mcontents.decode('utf-8')))
        result = run_median_analysis(df, median_table=median_df)
        result['insights'] = median_insights(result)
        result['recommendations'] = median_recommendations(result)
        result['timestamp'] = datetime.now().isoformat()
        return json_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


# --------------------------------------------------------------------------- #
# AI assistant (chatbot)
# --------------------------------------------------------------------------- #
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        return json_response(chat_answer(request.question, request.context or {}, request.history or []))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat/teach")
async def chat_teach_endpoint(request: TeachRequest):
    """Teach the assistant a better answer; it persists and reuses it."""
    try:
        count = chat_teach(request.question, request.answer)
        return json_response({'status': 'learned', 'total_taught': count})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/chat/taught")
def chat_taught():
    return json_response({'taught': load_taught()})


# --------------------------------------------------------------------------- #
# Downloadable templates / sample files (so users know the upload format)
# --------------------------------------------------------------------------- #
def _csv_response(df: pd.DataFrame, filename: str) -> Response:
    return Response(
        content=df.to_csv(index=False),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/template/employee")
def template_employee():
    """Blank-ish employee template with the exact required columns + 2 example rows."""
    df = pd.DataFrame([
        {'employee_id': 'EMP0001', 'job_title': 'Engineering L3', 'job_function': 'Engineering',
         'job_level': 'L3', 'location': 'Bangalore', 'base_salary': 2800000,
         'gender': 'Female', 'tenure_years': 4.5, 'performance_rating': 4.2},
        {'employee_id': 'EMP0002', 'job_title': 'Sales L2', 'job_function': 'Sales',
         'job_level': 'L2', 'location': 'Mumbai', 'base_salary': 1600000,
         'gender': 'Male', 'tenure_years': 2.0, 'performance_rating': 3.8},
    ])
    return _csv_response(df, 'employee_template.csv')


@app.get("/api/template/median")
def template_median():
    """Median-benchmark template (a couple of example rows)."""
    df = pd.DataFrame([
        {'job_function': 'Engineering', 'job_level': 'L3', 'median_salary': 3000000},
        {'job_function': 'Sales', 'job_level': 'L2', 'median_salary': 1650000},
    ])
    return _csv_response(df, 'median_template.csv')


@app.get("/api/download/sample-employees")
def download_sample_employees():
    return _csv_response(generate_sample_dataset(), 'sample_employees.csv')


@app.get("/api/download/sample-median")
def download_sample_median():
    return _csv_response(generate_median_reference(), 'sample_median_benchmark.csv')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
