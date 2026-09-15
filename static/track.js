const rollNoInput =
    document.getElementById("rollNo");

const searchBtn =
    document.getElementById("searchBtn");

const message =
    document.getElementById("message");

const complaintResult =
    document.getElementById("complaintResult");

const statusValue =
    document.getElementById("statusValue");


searchBtn.addEventListener(
    "click",
    loadComplaint
);


rollNoInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {
            loadComplaint();
        }

    }
);


async function loadComplaint() {

    const rollNo =
        rollNoInput.value.trim();


    message.innerText = "";

    complaintResult.style.display = "none";


    if (!rollNo) {

        message.className =
            "message error";

        message.innerText =
            "Please enter your university roll number.";

        return;
    }


    searchBtn.disabled = true;

    searchBtn.innerText =
        "Searching...";


    try {

        const response =
            await fetch(
                `/api/complaints?uni_roll_no=${encodeURIComponent(rollNo)}`
            );


        const data =
            await response.json();


        console.log(
            "TRACK RESPONSE:",
            data
        );


        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "Unable to find complaints."
            );

        }


        const complaints =
            data.complaints || [];


        if (!complaints.length) {

            throw new Error(
                "No complaints found for this roll number."
            );

        }


        const complaint =
            complaints[0];


        displayComplaint(
            complaint
        );


    } catch (error) {

        console.error(
            "Tracking error:",
            error
        );


        message.className =
            "message error";

        message.innerText =
            error.message;

    }


    searchBtn.disabled = false;

    searchBtn.innerText =
        "Track Complaint";
}


function displayComplaint(
    complaint
) {

    message.className =
        "message";


    message.innerText =
        "Complaint found.";


    complaintResult.style.display =
        "block";


    document.getElementById(
        "complaintId"
    ).innerText =
        `#${complaint.id}`;


    document.getElementById(
        "issue"
    ).innerText =
        complaint.issue ||
        complaint.description ||
        "—";


    document.getElementById(
        "category"
    ).innerText =
        complaint.category ||
        "—";


    document.getElementById(
        "department"
    ).innerText =
        complaint.department ||
        "—";


    document.getElementById(
        "location"
    ).innerText =
        complaint.location ||
        "—";


    document.getElementById(
        "priority"
    ).innerText =
        complaint.priority ||
        "—";


    document.getElementById(
        "updatedAt"
    ).innerText =
        formatDate(
            complaint.updated_at
        );


    document.getElementById(
        "recommendationText"
    ).innerText =
        complaint.recommended_action ||
        "No recommendation available.";


    updateStatus(
        complaint.status
    );
}


function updateStatus(
    status
) {

    if (!statusValue) {
        return;
    }

    const current =
        String(status || "Pending");

    statusValue.className =
        "status-value";

    statusValue.classList.add(
        current.toLowerCase().replaceAll(" ", "-")
    );

    statusValue.innerText =
        current;
}


function formatDate(
    value
) {

    if (!value) {
        return "—";
    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;

    }


    return date.toLocaleString();
}
