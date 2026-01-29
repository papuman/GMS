# Google AI Studio Instructions

To get the best results, you should provide Google AI Studio with two things:
1. **The Context** (The "Brain/Knowledge"): Use the `google_ai_studio_context.md` file I created.
2. **The Prompt** (The "Task"): Use the text below.

## Recommended Setup in Google AI Studio

1. **System Instructions** (Right-hand panel):
   *Copy and paste the entire content of `google_ai_studio_context.md` here.*
   *(This tells the AI "Here are the rules of Odoo 19 Design".)*

2. **Chat Prompt** (Main input box):
   *Copy and paste the text below here.*

---

## ✂️ START OF PROMPT ✂️

**Role:** You are an expert Odoo 19 UI/UX Designer and Frontend Developer. You specialize in the Point of Sale (POS) and Invoicing modules.

**Objective:** Design the UI/UX for a custom **Invoicing Module** that integrates seamlessly with our POS system.

**Constraints & Style Guide:**
*   You **MUST** strictly follow the Odoo 19 Enterprise design tokens provided in the System Instructions (Colors, Typography, Spacing).
*   **Color Palette:** Use the Enterprise Purple (`#714B67`) for main branding and Teal (`#017e84`) for primary actions. Do NOT use Community colors.
*   **Layout:** The design must be responsive. Use the "Split Pane" pattern (Left: Controls/Summary, Right: Workspace) familiar to Odoo POS users.
*   **Dark Mode:** Ensure all components have defined dark mode states (using `darken()` on backgrounds as specified).

**Task:**
Please generate the following deliverables:
1.  **Wireframe Description**: A text-based description of the layout for the main Invoicing Screen.
2.  **XML View Definition**: The Odoo QWeb XML code (`.xml`) to render this screen, using standard Odoo components (`<Numpad>`, `<ActionpadWidget>`, etc.).
3.  **SCSS Styles**: The SCSS code needed to style this screen, adhering to the variables in the context (e.g., using `$pos-left-pane-width`).

**Specific Feature Requirements (Derived from PRD):**

1.  **Hacienda E-Invoicing v4.4 Compliance (Priority 1):**
    *   **Status Dashboard:** A clear, three-state visual indicator for invoices: `Preparing` -> `Sent` -> `Approved/Rejected`. Avoid complex Odoo internal states.
    *   **One-Click Submission:** A prominent "Generate & Submit" button on the Invoice screen that handles XML generation, digital signature, and API submission in one action.
    *   **Error Handling:** If Hacienda rejects an invoice, display the error message in plain Spanish (e.g., "Invalid Tax ID") directly on the invoice form, with a "Retry" button.

2.  **POS Integration & Payment Reconciliation:**
    *   **SINPE Mobile Button:** On the POS Payment Screen, a dedicated "SINPE Mobile" payment method button.
    *   **Reference Field:** When SINPE is selected, a mandatory field to input the transaction reference number (or auto-filled if integrated).
    *   **Auto-Invoice Toggle:** A toggle on the POS payment screen: "Generar Factura Electrónica" (Generate E-Invoice). If checked, validating the POS order must automatically trigger the background e-invoice generation workflow.

3.  **Member Management in POS:**
    *   **Quick Check-in:** A simplified member search/lookup directly in the POS interface to check subscription status (Active/Inactive) before selling products.
    *   **Guest Pass:** A "Guest/Drop-in" product that immediately prompts for basic tax details (Name, ID, Email) required for the e-invoice.

Please start by outlining the Wireframe.
