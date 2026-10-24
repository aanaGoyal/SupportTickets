
import { useState } from "react";
import "./Support.css";

function Support() {
  const [subject, setSubject] = useState("");
  const [query, setQuery] = useState("");
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [ticketId, setTicketId] = useState("");
  const [ticketStatus, setTicketStatus] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await fetch("http://localhost:5000/api/support", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          subject: subject.trim(),
          query: query.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to submit your query.");
      }

      if (!data.ticketId) {
        throw new Error("The server did not return a ticket ID.");
      }

      setTicketId(data.ticketId);
      setTicketStatus(data.status || "open");
      setSubmitted(true);
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to customer support. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetForm() {
    setSubmitted(false);
    setSubject("");
    setQuery("");
    setEmail("");
    setTicketId("");
    setTicketStatus("");
    setError("");
  }

  if (submitted) {
    return (
      <main className="support-page">
        <section className="support-panel success-panel">
          <div className="success-icon">✓</div>
          <p className="support-eyebrow">AURORA BANK SUPPORT</p>
          <h1>Your query has been submitted!</h1>
          <p className="support-description">
            Your support ticket has been created successfully. Keep your
            ticket reference for future follow-up.
          </p>

          <div className="ticket-reference">
            <span>Ticket reference</span>
            <strong>{ticketId}</strong>
            <span>Status: {ticketStatus}</span>
          </div>

          <button
            className="support-primary"
            type="button"
            onClick={resetForm}
          >
            Submit another query
          </button>

          <a className="back-link" href="/">
            Back to Aurora Bank
          </a>
        </section>
      </main>
    );
  }

  return (
    <main className="support-page">
      <section className="support-intro">
        <p className="support-eyebrow">WE'RE HERE TO HELP</p>
        <h1>
          Let's get things <span>sorted.</span>
        </h1>
        <p className="support-description">
          Tell us what happened. Our customer support workflow will create
          a ticket so your query can be tracked.
        </p>

        <div className="support-promise">
          <span>✓</span>
          <div>
            <strong>Every query matters</strong>
            <p>We want to make getting help simpler.</p>
          </div>
        </div>
      </section>

      <section className="support-panel">
        <div className="form-heading">
          <p className="support-eyebrow">CUSTOMER CARE</p>
          <h2>Submit a query</h2>
          <p>Fields marked * are required.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email address *</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            required
          />

          <label htmlFor="subject">Subject *</label>
          <input
            id="subject"
            type="text"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            placeholder="e.g. Payment deducted twice"
            minLength={3}
            maxLength={200}
            required
          />

          <label htmlFor="query">Describe your issue *</label>
          <textarea
            id="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Please explain how we can help..."
            rows={6}
            maxLength={3000}
            required
          />

          <p className="privacy-note">
            Please don't include passwords, PINs, OTPs, or full card
            numbers in your message.
          </p>

          {error && (
            <p role="alert" className="support-error">
              {error}
            </p>
          )}

          <button
            className="support-primary"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Submitting..." : "Submit query"}
            {!isSubmitting && <span> ↗</span>}
          </button>
        </form>
      </section>
    </main>
  );
}

export default Support;
