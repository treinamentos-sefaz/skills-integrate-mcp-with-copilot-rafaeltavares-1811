document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupContainer = document.getElementById("signup-container");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const accountButton = document.getElementById("account-button");
  const accountMenu = document.getElementById("account-menu");
  const loginOpenButton = document.getElementById("login-open");
  const logoutButton = document.getElementById("logout-button");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginCancelButton = document.getElementById("login-cancel");
  const loginError = document.getElementById("login-error");
  let isTeacher = false;

  function showMessage(message, type) {
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");
    setTimeout(() => messageDiv.classList.add("hidden"), 5000);
  }

  function renderAuthState() {
    signupContainer.hidden = !isTeacher;
    loginOpenButton.hidden = isTeacher;
    logoutButton.hidden = !isTeacher;
  }

  async function refreshAuthState() {
    try {
      const response = await fetch("/auth/status");
      const status = await response.json();
      isTeacher = response.ok && status.authenticated === true;
    } catch (error) {
      isTeacher = false;
      console.error("Error checking teacher login:", error);
    }
    renderAuthState();
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.replaceChildren(activitySelect.options[0]);

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        const title = document.createElement("h4");
        title.textContent = name;
        const description = document.createElement("p");
        description.textContent = details.description;
        const schedule = document.createElement("p");
        const scheduleLabel = document.createElement("strong");
        scheduleLabel.textContent = "Schedule:";
        schedule.append(scheduleLabel, ` ${details.schedule}`);
        const availability = document.createElement("p");
        const availabilityLabel = document.createElement("strong");
        availabilityLabel.textContent = "Availability:";
        availability.append(availabilityLabel, ` ${spotsLeft} spots left`);

        const participantsContainer = document.createElement("div");
        participantsContainer.className = "participants-container";
        if (details.participants.length > 0) {
          const participantsSection = document.createElement("div");
          participantsSection.className = "participants-section";
          const participantsHeading = document.createElement("h5");
          participantsHeading.textContent = "Participants:";
          const participantsList = document.createElement("ul");
          participantsList.className = "participants-list";

          details.participants.forEach((email) => {
            const participantItem = document.createElement("li");
            const participantEmail = document.createElement("span");
            participantEmail.className = "participant-email";
            participantEmail.textContent = email;
            participantItem.appendChild(participantEmail);

            if (isTeacher) {
              const unregisterButton = document.createElement("button");
              unregisterButton.className = "delete-btn";
              unregisterButton.type = "button";
              unregisterButton.textContent = "❌";
              unregisterButton.setAttribute(
                "aria-label",
                `Unregister ${email} from ${name}`
              );
              unregisterButton.dataset.activity = name;
              unregisterButton.dataset.email = email;
              unregisterButton.addEventListener("click", handleUnregister);
              participantItem.appendChild(unregisterButton);
            }

            participantsList.appendChild(participantItem);
          });

          participantsSection.append(participantsHeading, participantsList);
          participantsContainer.appendChild(participantsSection);
        } else {
          const noParticipants = document.createElement("p");
          const noParticipantsText = document.createElement("em");
          noParticipantsText.textContent = "No participants yet";
          noParticipants.appendChild(noParticipantsText);
          participantsContainer.appendChild(noParticipants);
        }

        activityCard.append(
          title,
          description,
          schedule,
          availability,
          participantsContainer
        );

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.currentTarget;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        await fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  accountButton.addEventListener("click", () => {
    const isOpen = !accountMenu.classList.contains("hidden");
    accountMenu.classList.toggle("hidden", isOpen);
    accountButton.setAttribute("aria-expanded", String(!isOpen));
  });

  loginOpenButton.addEventListener("click", () => {
    accountMenu.classList.add("hidden");
    accountButton.setAttribute("aria-expanded", "false");
    loginError.hidden = true;
    loginDialog.showModal();
  });

  loginCancelButton.addEventListener("click", () => loginDialog.close());

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    loginError.hidden = true;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: document.getElementById("username").value,
          password: document.getElementById("password").value,
        }),
      });
      const result = await response.json();

      if (!response.ok) {
        loginError.textContent = result.detail || "Unable to log in.";
        loginError.hidden = false;
        return;
      }

      loginDialog.close();
      loginForm.reset();
      await refreshAuthState();
      await fetchActivities();
      showMessage("Logged in as a teacher.", "success");
    } catch (error) {
      loginError.textContent = "Unable to log in. Please try again.";
      loginError.hidden = false;
      console.error("Error logging in:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      const result = await response.json();
      if (!response.ok) {
        showMessage(result.detail || "Unable to log out.", "error");
        return;
      }

      isTeacher = false;
      renderAuthState();
      accountMenu.classList.add("hidden");
      accountButton.setAttribute("aria-expanded", "false");
      await fetchActivities();
      showMessage(result.message, "success");
    } catch (error) {
      showMessage("Unable to log out. Please try again.", "error");
      console.error("Error logging out:", error);
    }
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        await fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  refreshAuthState().then(fetchActivities);
});
