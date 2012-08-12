PYTHON='/Users/ratazzi/.runtime/bin/python'

app:
	@echo ">>> building ..."
	rm -rf build dist app
	arch -i386 python ~/Downloads/pyinstaller-1.5.1/Build.py app.spec
	cp dist/* ./
	@echo ">>> \033[01;32mdone.\033[00m"
