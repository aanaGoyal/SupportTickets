
const express = require("express");
const dotenv = require("dotenv");
const cors = require("cors");
dotenv.config();

const app = express();
const PORT = 5000;
app.use(
  cors({
    origin: "http://localhost:5173",
  })
);

app.use(express.json());

app.get("/health", (req, res) => {
  res.status(200).json({
    status: "healthy",
    service: "Aurora Bank Backend",
  });
});

// Receive a support request from Aurora Bank's frontend.
app.post("/api/support", async (req, res) => {
  try {
    const { subject, query } = req.body;

    if (
      typeof subject !== "string" ||
      subject.trim().length < 3 ||
      subject.trim().length > 200
    ) {
      return res.status(400).json({
        error: "Subject must be between 3 and 200 characters.",
      });
    }

    if (typeof query !== "string" || !query.trim()) {
      return res.status(400).json({
        error: "Please enter your support query.",
      });
    }

    if (query.length > 3000) {
      return res.status(400).json({
        error: "Support query cannot exceed 3000 characters.",
      });
    }

    const apiUrl = process.env.FIXFLOW_API_URL;
    const integrationKey = process.env.AURORA_INTEGRATION_KEY;

    if (!apiUrl || !integrationKey) {
      console.error("FixFlow integration configuration is missing.");

      return res.status(503).json({
        error: "Support service is temporarily unavailable.",
      });
    }

    const fixflowResponse = await fetch(
      `${apiUrl.replace(/\/+$/, "")}/api/v1/integrations/aurora/tickets`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${integrationKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          subject: subject.trim(),
          body: query.trim(),
        }),
        signal: AbortSignal.timeout(15000),
      }
    );

    const ticket = await fixflowResponse.json().catch(() => null);

    if (!fixflowResponse.ok) {
      console.error(
        "FixFlow ticket creation failed with status:",
        fixflowResponse.status
      );

      return res.status(502).json({
        error: "Unable to create your support ticket. Please try again.",
      });
    }

    return res.status(201).json({
      message: "Support ticket created successfully.",
      ticketId: ticket.id,
      status: ticket.status,
    });
  } catch (error) {
    console.error("Support request failed:", error.message);

    return res.status(502).json({
      error: "Unable to reach the support service. Please try again.",
    });
  }
});

app.listen(PORT, () => {
  console.log(`Aurora Bank backend running at http://localhost:${PORT}`);
});

