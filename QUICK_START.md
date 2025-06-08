# 🚀 SEC Filing Scanner - QUICK START

## For Impatient Users (2-Minute Setup)

### Windows Users:
1. **Double-click**: `setup.bat`
2. **Follow prompts** in the console window
3. **Done!** ✅

### Mac/Linux Users:
1. **Open terminal** in this directory
2. **Run**: `bash setup.sh`
3. **Follow prompts**
4. **Done!** ✅

### Python Users (All Platforms):
```bash
python setup_launcher.py
```
Then choose option 1 (Comprehensive Setup).

---

## What These Scripts Do

- ✅ **Check your system** (Python version, dependencies)
- ✅ **Install everything** needed automatically
- ✅ **Fix common issues** before they cause problems
- ✅ **Validate installation** works correctly
- ✅ **Set up directories** and configuration
- ✅ **Test all components** before finishing

---

## After Setup Completes

### Start the Application:

**Option 1 - Streamlit Only** (Easiest):
```bash
streamlit run streamlit_app.py
```
Then visit: http://localhost:8501

**Option 2 - Full Stack** (Backend + Frontend):
```bash
# Terminal 1:
uvicorn app.main:app --reload

# Terminal 2:
streamlit run streamlit_app.py
```

**Option 3 - Docker** (If you have Docker):
```bash
docker-compose -f docker/docker-compose.yml up
```

---

## Need Help?

- 📖 **Detailed Guide**: See `SETUP_README.md`
- 🔧 **Troubleshooting**: Run `python setup_and_check.py`
- 🐛 **Fix Issues**: Run `python debug_and_fix.py`
- 🆘 **Still Stuck**: Check the error messages and Google them

---

## Requirements Before Starting

1. **Python 3.8-3.11** installed
2. **Internet connection** (for downloading packages)
3. **OpenAI API Key** (get from: https://platform.openai.com/api-keys)
4. **Your email** (for SEC API requests)

---

**That's it! The setup scripts handle everything else automatically.**
