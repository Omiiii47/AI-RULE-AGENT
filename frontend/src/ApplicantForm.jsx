import { useState } from "react";
import { applyForLoan } from "./api";

const initialForm = {
  name: "",
  age: "",
  monthlySalary: "",
  creditScore: "",
  employmentType: "Salaried",
  loanAmount: "",
};

export default function ApplicantForm() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const payload = {
        name: form.name,
        age: Number(form.age),
        monthlySalary: Number(form.monthlySalary),
        creditScore: Number(form.creditScore),
        employmentType: form.employmentType,
        loanAmount: Number(form.loanAmount),
      };
      const data = await applyForLoan(payload);
      setResult(data);
    } catch (err) {
      setError("Something went wrong while checking eligibility. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const isEligible = result?.status === "Eligible";

  return (
    <div style={{ maxWidth: 480, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>Loan Eligibility Check</h2>
      <p style={{ color: "#666", marginTop: -8 }}>
        Fill in your details below to check if you qualify for a Personal Loan.
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <Field label="Full Name">
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            style={inputStyle}
          />
        </Field>

        <Field label="Age">
          <input
            type="number"
            name="age"
            value={form.age}
            onChange={handleChange}
            required
            min="0"
            style={inputStyle}
          />
        </Field>

        <Field label="Monthly Salary (₹)">
          <input
            type="number"
            name="monthlySalary"
            value={form.monthlySalary}
            onChange={handleChange}
            required
            min="0"
            style={inputStyle}
          />
        </Field>

        <Field label="Credit Score">
          <input
            type="number"
            name="creditScore"
            value={form.creditScore}
            onChange={handleChange}
            required
            min="300"
            max="900"
            style={inputStyle}
          />
        </Field>

        <Field label="Employment Type">
          <select
            name="employmentType"
            value={form.employmentType}
            onChange={handleChange}
            style={inputStyle}
          >
            <option value="Salaried">Salaried</option>
            <option value="Self-Employed">Self-Employed</option>
            <option value="Business Owner">Business Owner</option>
          </select>
        </Field>

        <Field label="Loan Amount Requested (₹)">
          <input
            type="number"
            name="loanAmount"
            value={form.loanAmount}
            onChange={handleChange}
            required
            min="0"
            style={inputStyle}
          />
        </Field>

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "10px 16px",
            marginTop: 8,
            background: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: 15,
          }}
        >
          {loading ? "Checking..." : "Check Eligibility"}
        </button>
      </form>

      {error && (
        <div style={{ marginTop: 16, color: "#dc2626" }}>{error}</div>
      )}

      {result && (
        <div
          style={{
            marginTop: 24,
            padding: 16,
            borderRadius: 8,
            background: isEligible ? "#ecfdf5" : "#fef2f2",
            border: `1px solid ${isEligible ? "#a7f3d0" : "#fecaca"}`,
          }}
        >
          <h3 style={{ margin: 0, color: isEligible ? "#047857" : "#b91c1c" }}>
            {isEligible ? "✅ Eligible" : "❌ Rejected"}
          </h3>

          {!isEligible && result.reasons?.length > 0 && (
            <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
              {result.reasons.map((reason, i) => (
                <li key={i} style={{ color: "#7f1d1d" }}>{reason}</li>
              ))}
            </ul>
          )}

          <div style={{ marginTop: 8, fontSize: 12, color: "#666" }}>
            Application ID: {result.applicationId}
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 14 }}>
      {label}
      {children}
    </label>
  );
}

const inputStyle = {
  padding: 8,
  borderRadius: 6,
  border: "1px solid #ccc",
  fontSize: 14,
};
