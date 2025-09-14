// Main JavaScript functionality
import L from "leaflet"
import Chart from "chart.js/auto"

class PotholesApp {
  constructor() {
    this.map = null
    this.markers = []
    this.init()
  }

  init() {
    // Initialize components based on page
    this.initializeMap()
    this.initializeCharts()
    this.initializeChat()
    this.initializeForms()
  }

  initializeMap() {
    const mapContainer = document.getElementById("map")
    if (!mapContainer) return

    // Default to a central location
    const defaultLat = 40.7128
    const defaultLng = -74.006

    this.map = L.map("map").setView([defaultLat, defaultLng], 10)

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
    }).addTo(this.map)

    // Load incidents on map
    this.loadIncidentsOnMap()
  }

  async loadIncidentsOnMap() {
    if (!this.map) return

    try {
      const response = await fetch("/incidents/api/incidents")
      const incidents = await response.json()

      incidents.forEach((incident) => {
        if (incident.latitude && incident.longitude) {
          const marker = L.marker([incident.latitude, incident.longitude]).addTo(this.map)

          const popupContent = `
                        <div>
                            <h6>${incident.location}</h6>
                            <p><strong>Severity:</strong> <span class="severity-${incident.severity}">${incident.severity}</span></p>
                            <p><strong>Status:</strong> <span class="badge status-${incident.status}">${incident.status}</span></p>
                            <p>${incident.description}</p>
                        </div>
                    `

          marker.bindPopup(popupContent)
          this.markers.push(marker)
        }
      })
    } catch (error) {
      console.error("Error loading incidents:", error)
    }
  }

  initializeCharts() {
    // Severity distribution chart
    const severityChart = document.getElementById("severityChart")
    if (severityChart) {
      this.createSeverityChart(severityChart)
    }

    // Status distribution chart
    const statusChart = document.getElementById("statusChart")
    if (statusChart) {
      this.createStatusChart(statusChart)
    }

    // Timeline chart
    const timelineChart = document.getElementById("timelineChart")
    if (timelineChart) {
      this.createTimelineChart(timelineChart)
    }
  }

  async createSeverityChart(canvas) {
    try {
      const response = await fetch("/dashboard/api/stats")
      const stats = await response.json()

      new Chart(canvas, {
        type: "doughnut",
        data: {
          labels: ["Critical", "Major", "Moderate", "Minor"],
          datasets: [
            {
              data: [
                stats.severity.critical || 0,
                stats.severity.major || 0,
                stats.severity.moderate || 0,
                stats.severity.minor || 0,
              ],
              backgroundColor: ["#ef4444", "#dc2626", "#f59e0b", "#06b6d4"],
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "bottom",
            },
          },
        },
      })
    } catch (error) {
      console.error("Error creating severity chart:", error)
    }
  }

  async createStatusChart(canvas) {
    try {
      const response = await fetch("/dashboard/api/stats")
      const stats = await response.json()

      new Chart(canvas, {
        type: "bar",
        data: {
          labels: ["Reported", "In Progress", "Resolved"],
          datasets: [
            {
              label: "Incidents",
              data: [stats.status.reported || 0, stats.status["in-progress"] || 0, stats.status.resolved || 0],
              backgroundColor: ["#f59e0b", "#06b6d4", "#10b981"],
            },
          ],
        },
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      })
    } catch (error) {
      console.error("Error creating status chart:", error)
    }
  }

  async createTimelineChart(canvas) {
    try {
      const response = await fetch("/dashboard/api/timeline")
      const timeline = await response.json()

      new Chart(canvas, {
        type: "line",
        data: {
          labels: timeline.labels,
          datasets: [
            {
              label: "New Incidents",
              data: timeline.data,
              borderColor: "#2563eb",
              backgroundColor: "rgba(37, 99, 235, 0.1)",
              tension: 0.4,
            },
          ],
        },
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      })
    } catch (error) {
      console.error("Error creating timeline chart:", error)
    }
  }

  initializeChat() {
    const chatForm = document.getElementById("chatForm")
    const chatMessages = document.getElementById("chatMessages")
    const chatInput = document.getElementById("chatInput")

    if (!chatForm) return

    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const message = chatInput.value.trim()
      if (!message) return

      // Add user message
      this.addChatMessage(message, "user")
      chatInput.value = ""

      // Show typing indicator
      const typingId = this.addChatMessage("Typing...", "bot", true)

      try {
        const response = await fetch("/chat/api/message", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message }),
        })

        const data = await response.json()

        // Remove typing indicator
        document.getElementById(typingId).remove()

        // Add bot response
        this.addChatMessage(data.response, "bot")
      } catch (error) {
        document.getElementById(typingId).remove()
        this.addChatMessage("Sorry, I encountered an error. Please try again.", "bot")
      }
    })
  }

  addChatMessage(message, sender, isTyping = false) {
    const chatMessages = document.getElementById("chatMessages")
    const messageId = "msg-" + Date.now()

    const messageDiv = document.createElement("div")
    messageDiv.id = messageId
    messageDiv.className = `message ${sender}`

    if (isTyping) {
      messageDiv.innerHTML = `<span class="loading-spinner"></span> ${message}`
    } else {
      messageDiv.textContent = message
    }

    chatMessages.appendChild(messageDiv)
    chatMessages.scrollTop = chatMessages.scrollHeight

    return messageId
  }

  initializeForms() {
    // Form validation and submission
    const forms = document.querySelectorAll("form[data-validate]")
    forms.forEach((form) => {
      form.addEventListener("submit", this.handleFormSubmit.bind(this))
    })

    // Location autocomplete
    const locationInputs = document.querySelectorAll("input[data-location]")
    locationInputs.forEach((input) => {
      this.initializeLocationAutocomplete(input)
    })
  }

  handleFormSubmit(e) {
    const form = e.target
    const submitBtn = form.querySelector('button[type="submit"]')

    if (submitBtn) {
      submitBtn.disabled = true
      submitBtn.innerHTML = '<span class="loading-spinner"></span> Processing...'
    }

    // Re-enable button after 3 seconds (fallback)
    setTimeout(() => {
      if (submitBtn) {
        submitBtn.disabled = false
        submitBtn.innerHTML = submitBtn.dataset.originalText || "Submit"
      }
    }, 3000)
  }

  initializeLocationAutocomplete(input) {
    // Simple location suggestions (in production, use a proper geocoding service)
    const suggestions = [
      "Main Street",
      "Broadway",
      "First Avenue",
      "Second Avenue",
      "Park Avenue",
      "Oak Street",
      "Elm Street",
      "Maple Avenue",
    ]

    input.addEventListener("input", (e) => {
      const value = e.target.value.toLowerCase()
      if (value.length < 2) return

      const matches = suggestions.filter((s) => s.toLowerCase().includes(value))

      // Create or update datalist
      let datalist = document.getElementById(input.id + "-suggestions")
      if (!datalist) {
        datalist = document.createElement("datalist")
        datalist.id = input.id + "-suggestions"
        input.setAttribute("list", datalist.id)
        input.parentNode.appendChild(datalist)
      }

      datalist.innerHTML = matches.map((match) => `<option value="${match}">`).join("")
    })
  }

  // Utility methods
  showAlert(message, type = "info") {
    const alertDiv = document.createElement("div")
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`
    alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `

    const container = document.querySelector(".container")
    if (container) {
      container.insertBefore(alertDiv, container.firstChild)
    }
  }

  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }
}

// Initialize app when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.potholesApp = new PotholesApp()
})
