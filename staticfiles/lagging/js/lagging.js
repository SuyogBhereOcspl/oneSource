// PSM checkbox select
function togglePSMMenu() {
    document.getElementById('psmMenuDropdown').classList.toggle('hidden');
  }

  document.addEventListener('click', function (event) {
    const dropdown = document.getElementById('psmMenuDropdown');
    const button = event.target.closest('button');
    if (dropdown && !dropdown.contains(event.target) && button === null) {
      dropdown.classList.add('hidden');
    }
  });




// Auto calculate RiskFactor
function calculateRiskFactor() {
    const severity = parseInt(document.getElementById("id_severity").value);
    const likelihood = parseInt(document.getElementById("id_likelihood").value);
    const risk_factorField = document.getElementById("id_risk_factor");

    if (!isNaN(severity) && !isNaN(likelihood)) {
        const risk_factorValue = severity * likelihood;
        
        if (risk_factorValue <= 2) {
            risk_factorField.value = `${risk_factorValue} - Low`;
            risk_factorField.style.backgroundColor = "#A7F3D0"; // Light Green
        } else if (risk_factorValue <= 6) {
            risk_factorField.value = `${risk_factorValue} - Medium`;
            risk_factorField.style.backgroundColor = "#FEF08A"; // Yellow
        } else {
            risk_factorField.value = `${risk_factorValue} - High`;
            risk_factorField.style.backgroundColor = "#FCA5A5"; // Red
        }
    } else {
        risk_factorField.value = "";
        risk_factorField.style.backgroundColor = "";
    }
}
// Attach event listeners to update Risk Factor dynamically
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("id_severity").addEventListener("change", calculateRiskFactor);
    document.getElementById("id_likelihood").addEventListener("change", calculateRiskFactor);
});




// Auto calculateMandaysLost
function calculateMandaysLost() {
    const incidentDate = new Date(document.getElementById("id_incident_date").value);
    const resumeDutyDate = new Date(document.getElementById("id_date_resume_duty").value);
    const mandaysLostField = document.getElementById("id_mandays_lost");

    if (!isNaN(incidentDate) && !isNaN(resumeDutyDate)) {
        const mandaysLostValue = Math.max(0, (resumeDutyDate - incidentDate) / (1000 * 60 * 60 * 24));
        mandaysLostField.value = mandaysLostValue;
    } else {
        mandaysLostField.value = "";
    }
}
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("id_incident_date").addEventListener("change", calculateMandaysLost);
    document.getElementById("id_date_resume_duty").addEventListener("change", calculateMandaysLost);
});




// Capa Entry add related code
document.addEventListener("DOMContentLoaded", function () {
    let capaContainer = document.getElementById("capa-container");
    let addCapaBtn = document.getElementById("add-capa");
    let totalForms = document.getElementById("id_{{ formset.prefix }}-TOTAL_FORMS");

    addCapaBtn.addEventListener("click", function () {
        let formNum = Number(totalForms.value);
        let newFormHtml = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">CAPA</label>
            <input type="text" name="{{ formset.prefix }}-__prefix__-capa" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Function</label>
            <select name="{{ formset.prefix }}-__prefix__-department" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
              <option value="">Select Department</option>
              <option value="ACCOUNTS">ACCOUNTS</option>
              <option value="BOILER UTILITY">BOILER UTILITY</option>
              <option value="ELECTRICAL">ELECTRICAL</option>
              <option value="EHS">EHS</option>
              <option value="HR ADMIN">HR ADMIN</option>
              <option value="INSTRUMENT">INSTRUMENT</option>
              <option value="IT">IT</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="OPERATION">OPERATION</OPERATION>
              <option value="PRODUCTION">PRODUCTION</option>
              <option value="QA/QC">QA/QC</QA/QC</option>
              <option value="SECURITY">SECURITY</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">FRP Name</label>
            <input type="text" name="{{ formset.prefix }}-__prefix__-frp" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">Compliance Status</label>
            <select name="{{ formset.prefix }}-__prefix__-compliance_status" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
              <option value="">Select Compliance Status</option>
              <option value="Open/Due">Open/Due</option>
              <option value="Closed">Closed</option>
              <option value="Overdue">Overdue</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Target Date</label>
            <input type="date" name="{{ formset.prefix }}-__prefix__-target_date" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline">
          </div>
          <div class="flex items-end justify-end">
            <button type="button" class="bg-red-500 text-white px-4 py-2 rounded remove-capa mt-4">Cancel</button>
          </div>
        </div>
        `.replace(/__prefix__/g, formNum);
        let div = document.createElement("div");
        div.classList.add("p-4", "bg-gray-50", "rounded", "mb-4", "capa-entry");

        // Insert the new form HTML properly
        div.innerHTML = newFormHtml;
        capaContainer.appendChild(div);
        
        // Update formset count
        totalForms.value = formNum + 1;

        // Ensure remove button works
        addRemoveEvent(div);
    });

    function addRemoveEvent(div) {
        let removeBtn = div.querySelector(".remove-capa");
        if (removeBtn) {
            removeBtn.addEventListener("click", function () {
                div.remove();
                totalForms.value = Number(totalForms.value) - 1;
            });
        }
    }
    // Attach remove event to existing forms
    document.querySelectorAll(".capa-entry").forEach(addRemoveEvent);
});





// compliense Status related code
function recalcComplianceStatus() {
    // Main compliance fields on the form
    let mainStatusField = document.getElementById("id_complience_status");
    let mainStatusDateField = document.getElementById("id_complience_status_date");

    // Get all CAPA compliance_status <select> fields
    let statusFields = document.querySelectorAll('select[name$="-compliance_status"]');

    // If 0 CAPA forms => leave main fields blank
    if (statusFields.length === 0) {
      mainStatusField.value = "";
      mainStatusDateField.value = "";
      return;
    }

    let foundOverdue = false;
    let foundOpen = false;
    let foundAnyRealStatus = false;  // Track if user actually selected a real status (not empty)

    // Check each CAPA compliance status
    statusFields.forEach(field => {
      // Ignore blank or "Select Compliance Status" => treat as unselected
      if (!field.value) return;

      foundAnyRealStatus = true;

      if (field.value === "Overdue") {
        foundOverdue = true;
      } else if (field.value === "Open/Due") {
        foundOpen = true;
      }
    });

    // If the user hasn't selected ANY real status for any CAPA => treat as no CAPAs
    if (!foundAnyRealStatus) {
      mainStatusField.value = "";
      mainStatusDateField.value = "";
      return;
    }

    // Now apply the main logic
    if (foundOverdue) {
      mainStatusField.value = "Overdue";
      mainStatusDateField.value = "";
    } else if (foundOpen) {
      mainStatusField.value = "Open/Due";
      mainStatusDateField.value = "";
    } else {
      // If none are Overdue or Open => set to Closed
      mainStatusField.value = "Closed";

      // Set compliance status date to today in YYYY-MM-DD
      let today = new Date();
      let yyyy = today.getFullYear();
      let mm = String(today.getMonth() + 1).padStart(2, '0');
      let dd = String(today.getDate()).padStart(2, '0');
      mainStatusDateField.value = `${yyyy}-${mm}-${dd}`;
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Recalculate whenever a CAPA compliance status changes
    let statusFields = document.querySelectorAll('select[name$="-compliance_status"]');
    statusFields.forEach(field => {
      field.addEventListener("change", recalcComplianceStatus);
    });

    // Run once on page load
    recalcComplianceStatus();
  });





