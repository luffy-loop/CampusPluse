const form = document.getElementById("complaintForm");
const result = document.getElementById("result");
const submitBtn = document.getElementById("submitBtn");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const rollNo = document.getElementById("rollNo").value.trim();
    const description = document.getElementById("description").value.trim();
    const isAnonymous = document.getElementById("anonymous").checked;
    const evidenceInput = document.getElementById("evidence");

    if (!rollNo || !description) {
        result.style.display = "block";
        result.className = "error";
        result.innerText = "Please fill in all required fields.";
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerText = "AI is analyzing your complaint...";
    result.style.display = "block";
    result.className = "loading";
    result.innerText = "Analyzing complaint and routing it to the right department...";

    try {
        const formData = new FormData();
        formData.append("description", description);
        formData.append("is_anonymous", isAnonymous);

        if (evidenceInput.files && evidenceInput.files.length > 0) {
            formData.append("evidence", evidenceInput.files[0]);
        }

        const response = await fetch("/api/complaints", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Something went wrong.");
        }

        const analysis = data.analysis;

        result.className = "success";
        result.innerHTML = `
            <div class="success-header">Complaint submitted successfully</div>
            <div class="complaint-id">Complaint ID: #${data.id}</div>
            <div class="ai-title">AI Complaint Analysis</div>
            <div class="analysis-grid">
                <div class="analysis-item"><span>Category</span><strong>${escapeHtml(analysis.category)}</strong></div>
                <div class="analysis-item"><span>Department</span><strong>${escapeHtml(analysis.department)}</strong></div>
                <div class="analysis-item"><span>Location</span><strong>${escapeHtml(analysis.location)}</strong></div>
                <div class="analysis-item"><span>Severity</span><strong>${analysis.severity}/10</strong></div>
                <div class="analysis-item"><span>Priority</span><strong>${escapeHtml(analysis.priority)}</strong></div>
                <div class="analysis-item"><span>Issue</span><strong>${escapeHtml(analysis.issue)}</strong></div>
            </div>
            <div class="recommendation">
                <span>Recommended Action</span>
                <p>${escapeHtml(analysis.recommended_action)}</p>
            </div>
            ${data.evidence_uploaded ? `<div class="evidence-success">Evidence attached successfully.</div>` : ""}
        `;

        form.reset();
    } catch (error) {
        console.error(error);
        result.className = "error";
        result.innerText = "Error: " + error.message;
    }

    submitBtn.disabled = false;
    submitBtn.innerText = "Submit Complaint";
});

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

const evidenceInput = document.getElementById("evidence");
const fileName = document.getElementById("fileName");
const fileHelp = document.getElementById("fileHelp");

if (evidenceInput) {
    evidenceInput.addEventListener("change", function () {
        if (this.files.length > 0) {
            const file = this.files[0];
            fileName.textContent = file.name;
            fileHelp.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB selected`;
        } else {
            fileName.textContent = "Attach a file";
            fileHelp.textContent = "Photo, screenshot or PDF";
        }
    });
}

const loadComplaintsBtn = document.getElementById("loadComplaintsBtn");
const myComplaintsList = document.getElementById("myComplaintsList");

function getMiniStatusClass(status) {
    if (status === "Resolved") {
        return "mini-resolved";
    }
    if (status === "In Progress") {
        return "mini-progress";
    }
    return "mini-pending";
}

async function loadMyComplaints() {
    const rollNo = document.getElementById("rollNo").value.trim();

    if (!rollNo) {
        myComplaintsList.innerHTML = `
            <div class="empty-complaints">
                <strong>Enter your university roll number</strong>
                <p>Your roll number is required to load your complaints.</p>
            </div>
        `;
        return;
    }

    loadComplaintsBtn.innerText = "Loading...";

    try {
        const response = await fetch(
            `/api/complaints?uni_roll_no=${encodeURIComponent(rollNo)}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Unable to load complaints.");
        }

        if (!data.complaints.length) {
            myComplaintsList.innerHTML = `
                <div class="empty-complaints">
                    <strong>No complaints found</strong>
                    <p>No complaints are associated with this roll number yet.</p>
                </div>
            `;
            return;
        }

        myComplaintsList.innerHTML = data.complaints.map(complaint => {
            const statusClass = getMiniStatusClass(complaint.status);

            return `
                <div class="complaint-mini-card">
                    <div class="mini-id">#${complaint.id}</div>
                    <div>
                        <div class="mini-description">${escapeHtml(complaint.description)}</div>
                        <div class="mini-meta">
                            ${escapeHtml(complaint.category || "Uncategorized")}
                            •
                            ${escapeHtml(complaint.location || "Location unavailable")}
                        </div>
                    </div>
                    <span class="mini-status ${statusClass}">
                        ${escapeHtml(complaint.status)}
                    </span>
                </div>
            `;
        }).join("");
    } catch (error) {
        console.error("My complaints error:", error);
        myComplaintsList.innerHTML = `
            <div class="empty-complaints">
                <strong>Unable to load complaints</strong>
                <p>Please try again.</p>
            </div>
        `;
    } finally {
        loadComplaintsBtn.innerText = "View My Complaints";
    }
}

if (loadComplaintsBtn) {
    loadComplaintsBtn.addEventListener("click", loadMyComplaints);
}