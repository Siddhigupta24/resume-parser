import os
import json
import csv
import io
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from openpyxl import Workbook
from config import MONGODB_URL, DATABASE_NAME
from services.file_service import validate_file, save_file, extract_text
from services.parser_service import parse_resume


router = APIRouter()
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]
collection = db["candidates"]


def format_candidate(doc) -> dict:
    result = dict(doc)
    result["id"] = str(result["_id"])
    del result["_id"]
    if "uploaded_at" in result:
        result["uploaded_at"] = str(result["uploaded_at"])
    return result


def build_clean_response(parsed_data: dict, inserted_id) -> dict:
    return {
        "name": parsed_data.get("name"),
        "email": parsed_data.get("email"),
        "phone": parsed_data.get("phone"),
        "location": parsed_data.get("location"),
        "city": parsed_data.get("city"),
        "country": parsed_data.get("country"),
        "linkedin": parsed_data.get("linkedin"),
        "github": parsed_data.get("github"),
        "portfolio": parsed_data.get("portfolio"),
        "skills": parsed_data.get("skills", []),
        "total_experience": parsed_data.get("total_experience"),
        "current_company": parsed_data.get("current_company"),
        "current_designation": parsed_data.get("current_designation"),
        "previous_companies": parsed_data.get("previous_companies", []),
        "previous_designations": parsed_data.get("previous_designations", []),
        "education": parsed_data.get("education", []),
        "certifications": parsed_data.get("certifications", []),
        "projects": parsed_data.get("projects", []),
        "profile_summary": parsed_data.get("profile_summary"),
        "file_name": parsed_data.get("file_name"),
        "parsing_status": parsed_data.get("parsing_status"),
        "accuracy_score": parsed_data.get("accuracy_score"),
        "missing_fields": parsed_data.get("missing_fields", []),
        "id": str(inserted_id),
        "uploaded_at": str(parsed_data.get("uploaded_at", "")),
    }


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_content = await file.read()

    is_valid, message = validate_file(file.filename, len(file_content))
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    existing = await collection.find_one({"file_name": file.filename})
    if existing:
        raise HTTPException(status_code=409, detail="A resume with this filename already exists.")

    unique_filename, file_path = save_file(file.filename, file_content)

    raw_text = extract_text(file_path)
    if not raw_text.strip():
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(status_code=422, detail="Could not extract text from this file.")

    try:
        parsed_data = parse_resume(raw_text)
    except Exception as e:
        try:
            os.remove(file_path)
        except:
            pass
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

    if not parsed_data:
        try:
            os.remove(file_path)
        except:
            pass
        raise HTTPException(status_code=500, detail="Parser returned empty result.")

    parsed_data["file_name"] = file.filename
    parsed_data["file_path"] = file_path

    result = await collection.insert_one(parsed_data)
    clean_response = build_clean_response(parsed_data, result.inserted_id)

    return {
        "message": "Resume uploaded and parsed successfully",
        "candidate_id": str(result.inserted_id),
        "parsing_status": clean_response["parsing_status"],
        "data": clean_response
    }


@router.get("/candidate/{candidate_id}")
async def get_candidate(candidate_id: str):
    try:
        object_id = ObjectId(candidate_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format.")

    doc = await collection.find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    return format_candidate(doc)


@router.get("/candidates")
async def search_candidates(
    name: str = None,
    skill: str = None,
    min_experience: float = None,
    max_experience: float = None,
    location: str = None,
    status: str = None,
    page: int = 1,
    limit: int = 100
):
    query = {}

    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    if skill:
        query["skills"] = {"$in": [skill]}

    if min_experience is not None:
        query.setdefault("total_experience", {})
        query["total_experience"]["$gte"] = min_experience

    if max_experience is not None:
        query.setdefault("total_experience", {})
        query["total_experience"]["$lte"] = max_experience

    if location:
        query["location"] = {"$regex": location, "$options": "i"}

    if status:
        query["parsing_status"] = status

    total = await collection.count_documents(query)
    skip = (page - 1) * limit
    cursor = collection.find(query).skip(skip).limit(limit)

    candidates = []
    async for doc in cursor:
        candidates.append(format_candidate(doc))

    return {"total": total, "page": page, "limit": limit, "candidates": candidates}


@router.put("/candidate/{candidate_id}")
async def update_candidate(candidate_id: str, updates: dict):
    try:
        object_id = ObjectId(candidate_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format.")

    # Only allow safe fields to be updated
    allowed_fields = {
        "name", "email", "phone", "location", "city", "country",
        "linkedin", "github", "portfolio", "skills", "total_experience",
        "current_company", "current_designation", "previous_companies",
        "previous_designations", "education", "certifications",
        "projects", "profile_summary", "parsing_status"
    }

    safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not safe_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update.")

    result = await collection.update_one(
        {"_id": object_id},
        {"$set": safe_updates}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    updated = await collection.find_one({"_id": object_id})
    return format_candidate(updated)


@router.delete("/candidate/{candidate_id}")
async def delete_candidate(candidate_id: str):
    try:
        object_id = ObjectId(candidate_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID format.")

    doc = await collection.find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Could not delete file: {e}")

    await collection.delete_one({"_id": object_id})
    return {"message": "Candidate deleted successfully"}


@router.get("/export")
async def export_candidates(format: str = "json"):
    cursor = collection.find({}).limit(10000)
    candidates = []
    async for doc in cursor:
        candidates.append(format_candidate(doc))

    if format == "json":
        content = json.dumps(candidates, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=candidates.json"}
        )

    elif format == "csv":
        output = io.StringIO()
        fieldnames = [
            "id", "name", "email", "phone", "location",
            "city", "country", "linkedin", "github", "portfolio",
            "skills", "total_experience", "current_company",
            "current_designation", "previous_companies",
            "parsing_status", "accuracy_score", "uploaded_at"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for c in candidates:
            row = dict(c)
            row["skills"] = ", ".join(c.get("skills", []))
            row["previous_companies"] = ", ".join(c.get("previous_companies", []))
            writer.writerow(row)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=candidates.csv"}
        )

    elif format == "excel":
        wb = Workbook()
        ws = wb.active
        ws.title = "Candidates"
        headers = [
            "ID", "Name", "Email", "Phone", "City", "Country", "Location",
            "LinkedIn", "GitHub", "Portfolio", "Skills", "Experience (Years)",
            "Current Company", "Current Designation", "Previous Companies",
            "Previous Designations", "Parsing Status", "Accuracy Score", "Uploaded At"
        ]
        ws.append(headers)
        for c in candidates:
            ws.append([
                c.get("id", ""), c.get("name", ""), c.get("email", ""),
                c.get("phone", ""), c.get("city", ""), c.get("country", ""),
                c.get("location", ""), c.get("linkedin", ""), c.get("github", ""),
                c.get("portfolio", ""), ", ".join(c.get("skills", [])),
                c.get("total_experience", ""), c.get("current_company", ""),
                c.get("current_designation", ""),
                ", ".join(c.get("previous_companies", [])),
                ", ".join(c.get("previous_designations", [])),
                c.get("parsing_status", ""), c.get("accuracy_score", ""),
                c.get("uploaded_at", ""),
            ])
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=candidates.xlsx"}
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use json, csv, or excel.")


@router.post("/reparse/{candidate_id}")
async def reparse_candidate(candidate_id: str):
    try:
        object_id = ObjectId(candidate_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID.")

    doc = await collection.find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    file_path = doc.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Resume file not found on disk.")

    raw_text = extract_text(file_path)
    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text.")

    parsed_data = parse_resume(raw_text)
    if not parsed_data:
        raise HTTPException(status_code=500, detail="Re-parsing failed.")

    parsed_data["file_name"] = doc.get("file_name")
    parsed_data["file_path"] = file_path

    await collection.update_one(
        {"_id": object_id},
        {"$set": {
            "name": parsed_data.get("name"),
            "email": parsed_data.get("email"),
            "phone": parsed_data.get("phone"),
            "location": parsed_data.get("location"),
            "city": parsed_data.get("city"),
            "country": parsed_data.get("country"),
            "linkedin": parsed_data.get("linkedin"),
            "github": parsed_data.get("github"),
            "portfolio": parsed_data.get("portfolio"),
            "skills": parsed_data.get("skills", []),
            "total_experience": parsed_data.get("total_experience"),
            "current_company": parsed_data.get("current_company"),
            "current_designation": parsed_data.get("current_designation"),
            "previous_companies": parsed_data.get("previous_companies", []),
            "previous_designations": parsed_data.get("previous_designations", []),
            "work_experience": parsed_data.get("work_experience", []),
            "education": parsed_data.get("education", []),
            "certifications": parsed_data.get("certifications", []),
            "projects": parsed_data.get("projects", []),
            "profile_summary": parsed_data.get("profile_summary"),
            "parsing_status": parsed_data.get("parsing_status"),
            "accuracy_score": parsed_data.get("accuracy_score"),
            "missing_fields": parsed_data.get("missing_fields", []),
        }}
    )

    return {
        "message": "Candidate re-parsed successfully",
        "candidate_id": candidate_id,
        "parsing_status": parsed_data.get("parsing_status"),
        "name": parsed_data.get("name")
    }


@router.post("/reparse-all")
async def reparse_all(limit: int = 100):
    cursor = collection.find({}).limit(limit)
    results = {"success": 0, "failed": 0, "skipped": 0}

    async for doc in cursor:
        file_path = doc.get("file_path")
        if not file_path or not os.path.exists(file_path):
            results["skipped"] += 1
            continue

        try:
            raw_text = extract_text(file_path)
            if not raw_text.strip():
                results["failed"] += 1
                continue

            parsed_data = parse_resume(raw_text)
            if not parsed_data:
                results["failed"] += 1
                continue

            await collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "name": parsed_data.get("name"),
                    "email": parsed_data.get("email"),
                    "phone": parsed_data.get("phone"),
                    "location": parsed_data.get("location"),
                    "city": parsed_data.get("city"),
                    "country": parsed_data.get("country"),
                    "linkedin": parsed_data.get("linkedin"),
                    "github": parsed_data.get("github"),
                    "portfolio": parsed_data.get("portfolio"),
                    "skills": parsed_data.get("skills", []),
                    "total_experience": parsed_data.get("total_experience"),
                    "current_company": parsed_data.get("current_company"),
                    "current_designation": parsed_data.get("current_designation"),
                    "previous_companies": parsed_data.get("previous_companies", []),
                    "previous_designations": parsed_data.get("previous_designations", []),
                    "work_experience": parsed_data.get("work_experience", []),
                    "education": parsed_data.get("education", []),
                    "certifications": parsed_data.get("certifications", []),
                    "projects": parsed_data.get("projects", []),
                    "profile_summary": parsed_data.get("profile_summary"),
                    "parsing_status": parsed_data.get("parsing_status"),
                    "accuracy_score": parsed_data.get("accuracy_score"),
                    "missing_fields": parsed_data.get("missing_fields", []),
                }}
            )
            results["success"] += 1
        except Exception as e:
            print(f"Failed: {doc.get('file_name')}: {e}")
            results["failed"] += 1

    return {"message": "Re-parse complete", "results": results}


@router.post("/upload-bulk")
async def upload_bulk(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        try:
            file_content = await file.read()

            is_valid, message = validate_file(file.filename, len(file_content))
            if not is_valid:
                results.append({"file_name": file.filename, "status": "Failed", "message": message})
                continue

            existing = await collection.find_one({"file_name": file.filename})
            if existing:
                results.append({"file_name": file.filename, "status": "Duplicate", "message": "Already exists in database"})
                continue

            unique_filename, file_path = save_file(file.filename, file_content)

            raw_text = extract_text(file_path)
            if not raw_text.strip():
                try:
                    os.remove(file_path)
                except:
                    pass
                results.append({"file_name": file.filename, "status": "Failed", "message": "Could not extract text"})
                continue

            try:
                parsed_data = parse_resume(raw_text)
            except Exception as e:
                try:
                    os.remove(file_path)
                except:
                    pass
                results.append({"file_name": file.filename, "status": "Failed", "message": f"Parsing error: {str(e)}"})
                continue

            if not parsed_data:
                try:
                    os.remove(file_path)
                except:
                    pass
                results.append({"file_name": file.filename, "status": "Failed", "message": "Parser returned empty result"})
                continue

            parsed_data["file_name"] = file.filename
            parsed_data["file_path"] = file_path

            result = await collection.insert_one(parsed_data)
            results.append({
                "file_name": file.filename,
                "status": "Success",
                "candidate_id": str(result.inserted_id),
                "name": parsed_data.get("name"),
                "parsing_status": parsed_data.get("parsing_status")
            })

        except Exception as e:
            results.append({"file_name": file.filename, "status": "Failed", "message": str(e)})

    return {
        "total": len(results),
        "successful": sum(1 for r in results if r["status"] == "Success"),
        "duplicates": sum(1 for r in results if r["status"] == "Duplicate"),
        "failed": sum(1 for r in results if r["status"] == "Failed"),
        "results": results
    }