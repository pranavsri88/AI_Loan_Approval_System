# 📱 Streamlit UI Navigation Guide

## Quick Access
🌐 **URL:** http://localhost:8501

---

## 🎯 The 3-Tab Interface

### TAB 1️⃣ - Application Form (Input)
**Purpose:** Submit loan applications

**What to do here:**
1. Fill in all applicant information fields
2. Enter loan details
3. Click **"Submit Application"** button
4. **THEN** switch to Tab 2 to see the decision

**Fields to fill:**
- Applicant ID (auto-generated)
- Age (slider: 18-80)
- Annual Income ($)
- Employment Type (dropdown)
- Credit Score (slider: 300-850)
- Loan Amount ($)
- Loan Tenure (months, slider)
- Existing Liabilities ($)
- Location (2-letter country code)

---

### TAB 2️⃣ - Decision Display (Output) ⭐ YOUR ANSWER IS HERE!
**Purpose:** View AI decision and analysis

**What you'll see:**
1. **Decision Badge** - The main result
   - ✅ **APPROVED** (green)
   - ⚠️ **REQUIRES_REVIEW** (yellow)
   - ❌ **REJECTED** (red)

2. **Risk Score Gauge** - Visual meter (0-100)
   - Shows overall risk level
   - Green (low risk) to Red (high risk)

3. **Confidence Percentage** - How certain the AI is
   - 0-100%
   - Higher = more confident in the decision

4. **Decision Factors Table** - Ranked list of factors
   - Factor name
   - Impact (positive/negative)
   - Contribution to score
   - Example: Credit Score, Employment Stability, DTI Ratio, etc.

5. **Detailed Explanation** - Human-readable reasoning
   - Why the decision was made
   - Key considerations
   - Risk factors

6. **Processing Time** - How long it took
   - Typical: 2-3 seconds

---

### TAB 3️⃣ - Audit Trail (History)
**Purpose:** View decision history and search records

**What you'll see:**
1. **Decision History Table** - All previous applications
2. **Search** - Find by Applicant ID
3. **Details per record:**
   - Applicant ID
   - Decision (APPROVED/REJECTED/REQUIRES_REVIEW)
   - Timestamp
   - Case ID
   - Risk Score
   - Confidence

---

## ⚡ Step-by-Step: How to Get Your Decision

### Step 1: Open the UI
Go to: **http://localhost:8501**

You'll see the **Application Form** (Tab 1) by default.

### Step 2: Fill in the Form
```
Age:                    35
Income:                 $85,000
Employment Type:        Salaried
Credit Score:           760
Loan Amount:            $150,000
Loan Tenure:            180 months
Existing Liabilities:   $12,000
Location:               US
```

### Step 3: Submit Application
Click the blue **"Submit Application"** button.

Wait 2-3 seconds for processing...

### Step 4: Switch to Tab 2 (Decision Display)
Look at the **TOP** of the page - you'll see 3 tabs:
- Application Form
- **Decision Display** ← Click here!
- Audit Trail

### Step 5: View Your Decision
You'll see:
- ✅/⚠️/❌ Decision badge
- Risk score meter
- Confidence percentage
- Decision factors
- Full explanation
- Processing time

---

## 📊 Example Decision Output

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│              ✅ DECISION: APPROVED                        │
│                                                            │
│              Risk Score: ▓▓▓░░░░░░░ 28/100              │
│              Confidence: 95.2%                            │
│                                                            │
│  Top Factors:                                             │
│  • Credit Score (790) - Excellent                         │
│  • Employment Stable (5+ years) - Positive                │
│  • DTI Ratio (0.32) - Favorable                           │
│  • Income Level ($150k) - Strong                          │
│  • LTI Ratio (1.33) - Low                                 │
│                                                            │
│  Explanation:                                             │
│  The applicant has a strong financial profile with        │
│  stable employment, excellent credit history, and         │
│  favorable debt ratios. The loan request is well within   │
│  acceptable parameters for approval.                      │
│                                                            │
│  Processing Time: 2.34 seconds                           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🆘 Troubleshooting

### Problem: Can't see Tab 2
**Solution:**
1. Refresh page (F5)
2. Clear cache (Ctrl+Shift+Delete)
3. Try incognito mode
4. Try different browser

### Problem: Streamlit not loading
**Check if running:**
```bash
ps aux | grep streamlit
```

**Restart Streamlit:**
```bash
pkill -f streamlit
cd /home/ubuntu/Desktop/demo/AI\ Loan\ Approval\ System
python3 -m streamlit run src/ui/streamlit_app.py --server.port=8501
```

**View logs:**
```bash
tail -f logs/streamlit.log
```

### Problem: Decision says "No data yet"
**Solution:**
1. Make sure you filled ALL fields in Tab 1
2. Click Submit Application
3. Wait 2-3 seconds
4. Switch to Tab 2
5. Refresh if needed

---

## 💡 Tips & Tricks

### Test Different Scenarios

**High-Confidence Approval:**
- Age: 45, Income: $150k, Credit: 790
- Loan: $200k, Tenure: 240 months
- Liabilities: $5k
- **Expected:** ✅ APPROVED (95%+)

**Marginal Case:**
- Age: 28, Income: $55k, Credit: 680
- Loan: $120k, Tenure: 24 months
- Liabilities: $18k
- **Expected:** ⚠️ REQUIRES_REVIEW

**Clear Rejection:**
- Age: 62, Income: $35k, Credit: 520
- Unemployed, Loan: $300k, Tenure: 12 months
- Liabilities: $80k
- **Expected:** ❌ REJECTED

### Audit Trail Features
- Search by Applicant ID
- View all previous decisions
- Sort by date, decision, risk score
- Export results (if enabled)

---

## 🎯 Understanding Decisions

### APPROVED ✅
- Strong financial profile
- Good credit score
- Stable employment
- Low debt ratios
- Confidence: 75%+

### REQUIRES_REVIEW ⚠️
- Borderline profile
- Some risk factors
- Needs manual review
- Confidence: 50-75%

### REJECTED ❌
- Significant risk factors
- Poor credit
- High debt ratios
- Unemployed
- Confidence: < 50% or multiple red flags

---

## 📞 Need Help?

1. **Check logs:**
   ```bash
   tail -f logs/app.log
   ```

2. **Verify services running:**
   ```bash
   ps aux | grep -E "(mcp|uvicorn|streamlit)"
   ```

3. **Test API directly:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/applications \
     -H "Content-Type: application/json" \
     -d '{"applicant_id": "TEST", "age": 35, ...}'
   ```

4. **API Documentation:**
   - Swagger: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## ✨ You're All Set!

**Next steps:**
1. Go to http://localhost:8501
2. Fill in the form
3. Click Submit
4. Click Tab 2 to see your decision
5. Explore Tab 3 for history

**Enjoy using the Agentic AI Loan Approval System! 🚀**
