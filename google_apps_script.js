/**
 * Google Apps Script for Student Academic Progression & Portfolio Management System
 * 
 * Instructions:
 * 1. Open your target Google Sheet.
 * 2. Click Extensions -> Apps Script.
 * 3. Replace all existing code with this script.
 * 4. Update SYNC_SECRET_TOKEN below if you customized it in .env.
 * 5. Click "Deploy" -> "New deployment" -> Select type "Web app".
 * 6. Set Description: "Student Academic Progression Sync Webhook".
 * 7. Set "Execute as": "Me".
 * 8. Set "Who has access": "Anyone" (Security is enforced via SYNC_SECRET_TOKEN inside the script).
 * 9. Click "Deploy", authorize access, and copy the Web App URL into your .env as GOOGLE_SHEETS_WEBHOOK_URL.
 */

const SYNC_SECRET_TOKEN = "kajal-academic-sync-token-2026";

const SCHEMAS = {
  Students: ["id", "student_code", "full_name", "email", "admission_year", "current_status", "created_at", "updated_at"],
  SchoolRecords: ["id", "student_id", "education_level", "institution", "board", "passing_year", "max_marks", "obtained_marks", "percentage", "created_at"],
  Semesters: ["id", "student_id", "semester_number", "academic_year", "credits", "sgpa", "cgpa", "created_at"],
  StudentMarks: ["id", "semester_id", "subject_code", "subject_name", "credits", "max_marks", "obtained_marks", "grade", "created_at"],
  GapYears: ["id", "student_id", "start_year", "end_year", "reason", "remarks", "created_at"],
  Seminars: ["id", "student_id", "title", "organizer", "event_date", "participation_type", "certificate_details", "created_at"],
  Activities: ["id", "student_id", "title", "category", "description", "event_date", "achievement", "certificate_details", "created_at"]
};

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ status: "error", message: "Empty POST body received" }, 400);
    }
    
    const payload = JSON.parse(e.postData.contents);
    
    // Authenticate token
    if (!payload.token || payload.token !== SYNC_SECRET_TOKEN) {
      return jsonResponse({ status: "error", message: "Unauthorized: Invalid or missing sync token" }, 401);
    }
    
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const action = payload.action;
    
    if (action === "bulk_sync") {
      const results = {};
      const tables = payload.tables || {};
      
      for (const [sheetName, headers] of Object.entries(SCHEMAS)) {
        const sheet = getOrCreateSheet(ss, sheetName, headers);
        const records = tables[sheetName] || [];
        
        // Clear old rows keeping header
        const lastRow = sheet.getLastRow();
        if (lastRow > 1) {
          sheet.getRange(2, 1, lastRow - 1, headers.length).clearContent();
        }
        
        if (records.length > 0) {
          const rows = records.map(rec => headers.map(h => rec[h] !== undefined && rec[h] !== null ? rec[h] : ""));
          sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
        }
        results[sheetName] = records.length;
      }
      
      return jsonResponse({
        status: "success",
        message: "Bulk synchronization completed successfully",
        synced_counts: results,
        timestamp: new Date().toISOString()
      });
    }
    
    if (action === "upsert_single") {
      const entity = payload.entity;
      const data = payload.data;
      if (!SCHEMAS[entity]) {
        return jsonResponse({ status: "error", message: "Unknown entity table: " + entity }, 400);
      }
      
      const headers = SCHEMAS[entity];
      const sheet = getOrCreateSheet(ss, entity, headers);
      const idVal = data.id;
      
      const rowValues = headers.map(h => data[h] !== undefined && data[h] !== null ? data[h] : "");
      
      // Look for existing ID in column 1
      const lastRow = sheet.getLastRow();
      let matchedRow = -1;
      if (lastRow > 1) {
        const idColValues = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
        for (let i = 0; i < idColValues.length; i++) {
          if (String(idColValues[i][0]) === String(idVal)) {
            matchedRow = i + 2;
            break;
          }
        }
      }
      
      if (matchedRow > 1) {
        sheet.getRange(matchedRow, 1, 1, headers.length).setValues([rowValues]);
        return jsonResponse({ status: "success", operation: "UPDATE", row: matchedRow, id: idVal });
      } else {
        sheet.appendRow(rowValues);
        return jsonResponse({ status: "success", operation: "INSERT", id: idVal });
      }
    }
    
    if (action === "delete_single") {
      const entity = payload.entity;
      const idVal = payload.data ? payload.data.id : payload.id;
      if (!SCHEMAS[entity]) {
        return jsonResponse({ status: "error", message: "Unknown entity table: " + entity }, 400);
      }
      
      const sheet = ss.getSheetByName(entity);
      if (!sheet) return jsonResponse({ status: "success", message: "Sheet not found, ignored" });
      
      const lastRow = sheet.getLastRow();
      if (lastRow > 1) {
        const idColValues = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
        for (let i = 0; i < idColValues.length; i++) {
          if (String(idColValues[i][0]) === String(idVal)) {
            sheet.deleteRow(i + 2);
            return jsonResponse({ status: "success", operation: "DELETE", id: idVal });
          }
        }
      }
      return jsonResponse({ status: "success", operation: "NOT_FOUND", id: idVal });
    }
    
    return jsonResponse({ status: "error", message: "Unsupported action: " + action }, 400);
    
  } catch (err) {
    return jsonResponse({ status: "error", message: err.toString() }, 500);
  }
}

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    service: "Student Academic Progression Sheets Webhook",
    status: "active",
    sheets: Object.keys(SCHEMAS),
    timestamp: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

function getOrCreateSheet(ss, sheetName, headers) {
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  // Setup headers if sheet is empty or row 1 doesn't have correct header count
  if (sheet.getLastRow() === 0 || sheet.getLastColumn() === 0) {
    sheet.appendRow(headers);
    const headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setFontWeight("bold");
    headerRange.setBackground("#0d9488"); // Teal accent
    headerRange.setFontColor("#ffffff");
  }
  return sheet;
}

function jsonResponse(data, code) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
