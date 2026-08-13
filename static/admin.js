const signalsList =
    document.getElementById("signalsList");

const totalComplaints =
    document.getElementById("totalComplaints");

const pendingComplaints =
    document.getElementById("pendingComplaints");

const highPriority =
    document.getElementById("highPriority");

const resolvedComplaints =
    document.getElementById("resolvedComplaints");

const attentionCount =
    document.getElementById("attentionCount");

const departmentList =
    document.getElementById("departmentList");

const complaintTable =
    document.getElementById("complaintTable");

const lastUpdated =
    document.getElementById("lastUpdated");

const briefingContent =
    document.getElementById("briefingContent");

const refreshBtn =
    document.getElementById("refreshBtn");


async function loadDashboard() {

    refreshBtn.innerText = "Refreshing...";

    try {

        const response =
            await fetch("/api/admin/dashboard");

        const data =
            await response.json();


        if (!data.success) {

            throw new Error(data.error);

        }


        // -------------------------
        // Statistics
        // -------------------------

        totalComplaints.innerText =
            data.stats.total;

        pendingComplaints.innerText =
            data.stats.pending;

        highPriority.innerText =
            data.stats.high_priority;

        resolvedComplaints.innerText =
            data.stats.resolved;

        attentionCount.innerText =
            data.stats.high_priority;


        // -------------------------
        // Departments
        // -------------------------

        renderDepartments(
            data.departments
        );


        // -------------------------
        // Complaints
        // -------------------------

        renderComplaints(
            data.complaints
        );

        await loadCampusSignals();

        await loadAIBriefing();

        lastUpdated.innerText =
            "Updated just now";


    } catch (error) {

        console.error(error);

        complaintTable.innerHTML = `
            <tr>
                <td colspan="8">
                    Unable to load dashboard data.
                </td>
            </tr>
        `;

    }

    refreshBtn.innerText = "Refresh Data";
}


function renderDepartments(departments) {

    if (!departments.length) {

        departmentList.innerHTML =
            `<p class="loading">No data yet.</p>`;

        return;

    }


    const maximum =
        Math.max(
            ...departments.map(
                item => item.count
            )
        );


    departmentList.innerHTML =
        departments.map(item => {

            const percentage =
                maximum === 0
                    ? 0
                    : (item.count / maximum) * 100;


            return `

                <div class="department-row">

                    <div class="department-top">

                        <strong>
                            ${escapeHtml(item.department)}
                        </strong>

                        <span>
                            ${item.count}
                        </span>

                    </div>

                    <div class="department-bar">

                        <div
                            class="department-fill"
                            style="width:${percentage}%"
                        ></div>

                    </div>

                </div>

            `;

        }).join("");
}


function renderComplaints(complaints) {

    if (!complaints.length) {

        complaintTable.innerHTML = `

            <tr>

                <td colspan="8">

                    No complaints submitted yet.

                </td>

            </tr>

        `;

        return;

    }


    complaintTable.innerHTML =
        complaints.map(item => {

            return `

                <tr>

                    <td>
                        #${item.id}
                    </td>


                    <td class="issue-cell">

                        ${escapeHtml(
                            item.description
                        )}

                    </td>


                    <td>

                        ${escapeHtml(
                            item.location || "Unknown"
                        )}

                    </td>


                    <td>

                        ${escapeHtml(
                            item.department || "Unassigned"
                        )}

                    </td>


                    <td>

                        ${item.severity ?? "—"}/10

                    </td>


                    <td>

                        ${priorityBadge(
                            item.priority
                        )}

                    </td>


                    
                        <td>
    <select
        class="status-select"
        value="${item.status || "Pending"}"
        onchange="updateComplaintStatus(${item.id}, this.value)"
    >
        <option value="Pending"
            ${item.status === "Pending" ? "selected" : ""}>
            Pending
        </option>

        <option value="In Progress"
            ${item.status === "In Progress" ? "selected" : ""}>
            In Progress
        </option>

        <option value="Resolved"
            ${item.status === "Resolved" ? "selected" : ""}>
            Resolved
        </option>
    </select>
</td>

                        <td>

    ${item.created_at || "—"}

</td>

<td>

    ${
        item.evidence_path
            ? `
                <a
                    href="/${item.evidence_path}"
                    target="_blank"
                    class="evidence-btn"
                >
                    View Evidence
                </a>
            `
            : `
                <span class="no-evidence">
                    No evidence
                </span>
            `
    }

            </td>
                <td>

    <span
        id="sla-${item.id}"
        class="sla-badge sla-loading"
    >
        Checking...
    </span>

</td>
                </tr>

            `;

        }).join("");
}


function priorityBadge(priority) {

    if (!priority) {
        return "—";
    }

    const value =
        priority.toLowerCase();

    let className =
        "badge-medium";


    if (value === "critical") {
        className = "badge-critical";
    }

    else if (value === "high") {
        className = "badge-high";
    }

    else if (value === "low") {
        className = "badge-low";
    }


    return `
        <span class="badge ${className}">
            ${escapeHtml(priority)}
        </span>
    `;
}


function statusBadge(status) {

    if (!status) {
        return "—";
    }


    const value =
        status.toLowerCase();


    let className =
        "badge-pending";


    if (value === "resolved") {
        className = "badge-resolved";
    }


    return `
        <span class="badge ${className}">
            ${escapeHtml(status)}
        </span>
    `;
}


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


refreshBtn.addEventListener(
    "click",
    loadDashboard
);


loadDashboard();

async function updateComplaintStatus(complaintId, newStatus) {

    try {

        const response = await fetch(
            `/api/admin/complaints/${complaintId}/status`,
            {
                method: "PUT",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    status: newStatus
                })
            }
        );

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error);
        }

        // Reload dashboard data
        await loadDashboard();

    } catch (error) {

        console.error(error);

        alert(
            "Unable to update complaint status: " +
            error.message
        );
    }
}

async function loadCampusSignals() {

    try {

        const response =
            await fetch("/api/admin/signals");

        const data =
            await response.json();


        if (!data.success) {
            throw new Error(data.error);
        }


        renderCampusSignals(
            data.signals
        );


    } catch (error) {

        console.error(
            "Campus Signals error:",
            error
        );

        signalsList.innerHTML = `
            <p class="loading">
                Unable to load campus signals.
            </p>
        `;
    }
}

function renderCampusSignals(signals) {

    if (!signals.length) {

        signalsList.innerHTML = `

            <div class="no-signals">

                <div class="no-signals-icon">
                    —
                </div>

                <div>

                    <strong>
                        No recurring issues detected
                    </strong>

                    <p>
                        Campus Pulse will surface a signal
                        when multiple complaints point to
                        the same location and category.
                    </p>

                </div>

            </div>

        `;

        return;
    }


    signalsList.innerHTML =
        signals.map(signal => {

            const priorityClass =
                getSignalPriorityClass(
                    signal.priority
                );


            return `

                <div class="signal-card">

                    <div class="signal-card-top">

                        <div>

                            <span class="signal-location">
                                ${escapeHtml(
                                    signal.location
                                )}
                            </span>

                            <h3>
                                ${escapeHtml(
                                    signal.category
                                )}
                            </h3>

                        </div>


                        <span
                            class="signal-priority ${priorityClass}"
                        >
                            ${escapeHtml(
                                signal.priority
                            )}
                        </span>

                    </div>


                    <div class="signal-meta">

                        <div>

                            <strong>
                                ${signal.complaint_count}
                            </strong>

                            <span>
                                complaints
                            </span>

                        </div>


                        <div>

                            <strong>
                                ${signal.average_severity}/10
                            </strong>

                            <span>
                                avg. severity
                            </span>

                        </div>


                        <div>

                            <strong>
                                ${escapeHtml(
                                    signal.department
                                )}
                            </strong>

                            <span>
                                responsible department
                            </span>

                        </div>

                    </div>


                    <div class="signal-footer">

                        <span>
                            Recurring issue detected
                        </span>

                        <span>
                            ${escapeHtml(
                                signal.location
                            )}
                        </span>

                    </div>

                </div>

            `;

        }).join("");

}

function getSignalPriorityClass(priority) {

    switch (priority) {

        case "Critical":
            return "signal-critical";

        case "High":
            return "signal-high";

        case "Medium":
            return "signal-medium";

        default:
            return "signal-low";
    }
}

async function loadAIBriefing() {

    try {

        const response =
            await fetch("/api/admin/briefing");

        const data =
            await response.json();

        if (!data.success) {
            throw new Error(data.error);
        }

        renderAIBriefing(
            data.briefing
        );

    } catch (error) {

        console.error(
            "AI briefing error:",
            error
        );

        briefingContent.innerHTML = `
            <p class="loading">
                Unable to generate the AI briefing.
            </p>
        `;
    }
}

function renderAIBriefing(briefing) {

    const urgencyClass =
        briefing.urgency
            .toLowerCase()
            .replace(" ", "-");

    briefingContent.innerHTML = `

        <div class="briefing-headline">

            <div>

                <h3>
                    ${escapeHtml(
                        briefing.headline
                    )}
                </h3>

                <p>
                    ${escapeHtml(
                        briefing.summary
                    )}
                </p>

            </div>

            <span class="briefing-urgency ${urgencyClass}">
                ${escapeHtml(
                    briefing.urgency
                )}
            </span>

        </div>


        <div class="briefing-grid">

            <div class="briefing-item">

                <span>
                    TOP ISSUE
                </span>

                <strong>
                    ${escapeHtml(
                        briefing.top_issue
                    )}
                </strong>

            </div>


            <div class="briefing-item">

                <span>
                    AFFECTED LOCATION
                </span>

                <strong>
                    ${escapeHtml(
                        briefing.affected_location
                    )}
                </strong>

            </div>


            <div class="briefing-item">

                <span>
                    RESPONSIBLE DEPARTMENT
                </span>

                <strong>
                    ${escapeHtml(
                        briefing.affected_department
                    )}
                </strong>

            </div>

        </div>


        <div class="briefing-action">

            <span>
                RECOMMENDED ACTION
            </span>

            <p>
                ${escapeHtml(
                    briefing.recommended_action
                )}
            </p>

        </div>

    `;
}
async function loadComplaintSLA(complaintId) {

    try {

        const response = await fetch(
            `/api/admin/complaints/${complaintId}/sla`
        );

        const data = await response.json();

        const element =
            document.getElementById(`sla-${complaintId}`);


        if (!element) {
            return;
        }


        if (!data.success) {

            element.innerText = "Unavailable";

            element.className =
                "sla-badge sla-loading";

            return;
        }


        element.innerText =
            data.sla_status;

        element.className =
            "sla-badge " +
            getSLAClass(data.sla_status);


    } catch (error) {

        console.error(
            "SLA error:",
            error
        );

    }
}


function getSLAClass(status) {

    switch (status) {

        case "Breached":
            return "sla-breached";

        case "At Risk":
            return "sla-risk";

        case "Resolved":
            return "sla-resolved";

        default:
            return "sla-on-track";
    }
}
