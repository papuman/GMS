# Quick Start: Odoo Validation (Day 1-2)

**Goal:** Get Odoo running locally in the next 2-3 hours

---

## ⚡ Fast Track Setup

### **Step 1: Install Prerequisites (15 minutes)**

Open Terminal and run:

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install prerequisites
brew install postgresql@13
brew install python@3.11
brew install node
brew install wkhtmltopdf

# Start PostgreSQL
brew services start postgresql@13

# Verify installations
psql --version  # Should show PostgreSQL 13.x
python3 --version  # Should show Python 3.11.x
node --version  # Should show Node v18+ or v20+
```

---

### **Step 2: Clone Odoo (5 minutes)**

```bash
# Create workspace
mkdir -p ~/Projects/odoo-gms-validation
cd ~/Projects/odoo-gms-validation

# Clone Odoo 19.0 (shallow clone for speed)
git clone https://github.com/odoo/odoo.git --depth 1 --branch 19.0
cd odoo
```

---

### **Step 3: Setup Python Environment (10 minutes)**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your terminal prompt

# Upgrade pip
pip install --upgrade pip wheel

# Install Odoo dependencies
pip install -r requirements.txt

# This will take 5-10 minutes - lots of packages!
```

**⚠️ Common Issues:**
- **Error with psycopg2:** Make sure PostgreSQL@13 is installed via Homebrew
- **Permission errors:** Don't use `sudo` - work within virtual environment

---

### **Step 4: Create Database (2 minutes)**

```bash
# Create PostgreSQL database
createdb gms_validation

# Verify it was created
psql -l | grep gms_validation
```

---

### **Step 5: Start Odoo (First Time - 15 minutes)**

```bash
# Make sure you're in the odoo directory and venv is activated
cd ~/Projects/odoo-gms-validation/odoo
source venv/bin/activate

# Start Odoo (this will initialize the database)
./odoo-bin -d gms_validation -i base --addons-path=addons --db-filter=gms_validation

# You should see:
# INFO ? odoo.modules.loading: loading 1 modules...
# INFO ? odoo.modules.loading: 1 modules loaded in X.XXs
# ...
# INFO ? odoo.http: HTTP service (werkzeug) running on http://0.0.0.0:8069
```

**Leave this terminal running!**

---

### **Step 6: Access Odoo (5 minutes)**

1. Open browser: http://localhost:8069

2. **First-time setup screen appears:**
   - Master Password: Create strong password (save it!)
   - Database Name: `gms_validation` (should be pre-filled)
   - Email: your email
   - Password: your admin password
   - Language: English
   - Country: Costa Rica ⭐
   - Click "Create Database"

3. **Wait 2-3 minutes** for database initialization

4. **You're in!** You should see Odoo dashboard

---

### **Step 7: Install Key Modules (30 minutes)**

Click **Apps** in the top menu

**Search and install these (one by one):**

1. ✅ **Accounting** - Click "Activate"
   - When prompted, select Costa Rica
   - Wait for installation (~2 min)

2. ✅ **Sales Management** - Click "Activate"
   - Enable Subscriptions when prompted
   - Wait for installation (~2 min)

3. ✅ **Point of Sale** - Click "Activate"
   - Wait for installation (~2 min)

4. ✅ **CRM** - Click "Activate"
   - Wait for installation (~1 min)

5. ✅ **Website** - Click "Activate"
   - Wait for installation (~3 min)

6. ✅ **Calendar** - Click "Activate"

7. ✅ **Inventory** - Click "Activate"

8. ✅ **Loyalty** - Click "Activate"

9. ✅ **Employees** (HR) - Click "Activate"

**After each installation:**
- Top-right corner will show "Installing..."
- Wait for it to complete
- Click "Apps" again to install next module

---

## ✅ Validation Checkpoint

**You've successfully completed Day 1-2 setup if:**

- ✅ Odoo is running at http://localhost:8069
- ✅ You can login as admin
- ✅ All 9 modules are installed (check Apps menu - filter by "Installed")
- ✅ You see these apps in your menu: Accounting, Sales, Point of Sale, CRM, Website, Calendar, Inventory, Loyalty, Employees

---

## 🎯 Next Steps

### **Day 3: Basic Configuration**

Now that Odoo is running, configure your gym:

1. **Settings → General Settings → Companies**
   - Update company name to "Gimnasio Demo"
   - Verify Country: Costa Rica
   - Add address, phone, email

2. **Accounting → Configuration → Settings**
   - Verify Fiscal Localization: Costa Rica
   - Check Taxes: Should have 13%, 4%, 2%, 1%, exempt

3. **Sales → Configuration → Settings**
   - Enable: Quotations & Orders
   - Enable: Subscriptions

4. **Point of Sale → Configuration**
   - Create POS: "Gym Retail Counter"
   - Set payment methods: Cash, Credit Card

---

## 🆘 Troubleshooting

### **Odoo won't start**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# If not running:
brew services start postgresql@13

# Check if port 8069 is in use
lsof -i :8069

# If something is using it, kill that process or use different port:
./odoo-bin -d gms_validation --http-port=8070
```

### **Can't create database**
```bash
# Make sure you have PostgreSQL user
createuser -s $USER

# Try creating database again
createdb gms_validation
```

### **Module installation fails**
- Check terminal where Odoo is running for error messages
- Try installing one module at a time
- Restart Odoo and try again

### **Forgot admin password**
```bash
# Stop Odoo (Ctrl+C in terminal)

# Reset password via command line
./odoo-bin -d gms_validation --db-filter=gms_validation shell

# In Python shell:
>>> self.env['res.users'].browse(2).write({'password': 'newpassword'})
>>> exit()

# Start Odoo again
./odoo-bin -d gms_validation --db-filter=gms_validation
```

---

## 💡 Useful Commands

```bash
# Start Odoo (normal)
cd ~/Projects/odoo-gms-validation/odoo
source venv/bin/activate
./odoo-bin -d gms_validation --db-filter=gms_validation

# Start Odoo with auto-reload (for development)
./odoo-bin -d gms_validation --db-filter=gms_validation --dev=all

# Update a specific module
./odoo-bin -d gms_validation -u account --stop-after-init

# Stop Odoo
# Press Ctrl+C in the terminal where Odoo is running
```

---

## 📚 Resources

- **Full Validation Plan:** docs/validation-plan.md
- **Odoo Documentation:** https://www.odoo.com/documentation/19.0/
- **Odoo Tutorials:** https://www.odoo.com/slides/
- **Community Forum:** https://www.odoo.com/forum/help-1

---

## ⏱️ Time Estimate

- **Prerequisites:** 15 min
- **Clone Odoo:** 5 min
- **Python Setup:** 10 min
- **Database:** 2 min
- **First Start:** 15 min
- **Access & Config:** 5 min
- **Install Modules:** 30 min

**Total:** ~90 minutes (1.5 hours)

---

**Ready to test? Continue with Week 2 in the full validation plan!**

When you're done with Day 1-2 setup, ping me and we'll move to the actual feature testing. 🏋️
