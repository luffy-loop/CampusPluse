const trackBtn =
    document.getElementById("trackBtn");

const complaintId =
    document.getElementById("complaintId");

const message =
    document.getElementById("message");

const complaintResult =
    document.getElementById("complaintResult");


trackBtn.addEventListener(
    "click",
    trackComplaint
);


complaintId.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {
            trackComplaint();
        }

    }
);


async function trackComplaint() {

    const id =
        complaintId.value.trim();


    if (!id) {

        message.className = "message error";

        message.innerText =
            "Enter a complaint ID.";

        complaintResult.style.display = "none";

        return;
    }


    trackBtn.disabled = true;

    trackBtn.innerText = "Searching...";

    message.innerText = "";

    complaintResult.style.display = "none";


    try {

        const response =
            await fetch(
                `/api/complaints/${id}`
            );


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.error
            );

        }


        renderComplaint(
            data.complaint
        );


    } catch (error) {

        message.className =
            "message error";

        message.innerText =
            error.message;

    }


    trackBtn.disabled = false;

    trackBtn.innerText =
        "Track Complaint";
}


function renderComplaint(complaint) {

    const status =
        complaint.status || "Pending";


    const pendingClass =
        "status-step " +
        (
            status === "Pending"
                ? "active"
                : status === "In Progress" ||
                  status === "Resolved"
                    ? "complete"
                    : ""
        );


    const progressClass =
        "status-step " +
        (
            status === "In Progress"
                ? "active"
                : status === "Resolved"
                    ? "complete"
                    : ""
        );


    const resolvedClass =
        "status-step " +
        (
            status === "Resolved"
                ? "complete"
                : ""
        );


    complaintResult.innerHTML = `

        <div class="result-header">

            <h2>
                Complaint Status
            </h2>

            <span class="complaint-id">
                #${complaint.id}
            </span>

        </div>


        <div class="status-track">

            <div class="${pendingClass}">
                Submitted
            </div>

            <div class="${progressClass}">
                In Progress
            </div>

            <div class="${resolvedClass}">
                Resolved
            </div>

        </div>


        <div class="details-grid">

            <div class="detail">

                <span>
                    Category
                </span>

                <strong>
                    ${escapeHtml(
                        complaint.category
                    )}
                </strong>

            </div>


            <div class="detail">

                <span>
                    Department
                </span>

                <strong>
                    ${escapeHtml(
                        complaint.department
                    )}
                </strong>

            </div>


            <div class="detail">

                <span>
                    Location
                </span>

                <strong>
                    ${escapeHtml(
                        complaint.location
                    )}
                </strong>

            </div>


            <div class="detail">

                <span>
                    Priority
                </span>

                <strong>
                    ${escapeHtml(
                        complaint.priority
                    )}
                </strong>

            </div>


            <div class="detail">

                <span>
                    Severity
                </span>

                <strong>
                    ${complaint.severity}/10
                </strong>

            </div>


            <div class="detail">

                <span>
                    Submitted
                </span>

                <strong>
                    ${escapeHtml(
                        complaint.created_at
                    )}
                </strong>

            </div>

        </div>


        <div class="recommendation">

            <span>
                Issue
            </span>

            <p>
                ${escapeHtml(
                    complaint.issue
                )}
            </p>

        </div>


        <div class="recommendation">

            <span>
                Recommended Action
            </span>

            <p>
                ${escapeHtml(
                    complaint.recommended_action
                )}
            </p>

        </div>

    `;


    complaintResult.style.display =
        "block";
}


function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}