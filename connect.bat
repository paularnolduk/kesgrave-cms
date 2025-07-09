@echo off
cd /d "C:\Users\Home\Documents\Websites\kesgrave"
python -c "import sys; sys.path.insert(0, '.'); import cms_final_complete; cms_final_complete.app.run(debug=True, host='0.0.0.0', port=8027)"
pause
