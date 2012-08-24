PYTHON='/Users/ratazzi/.runtime/bin/python'

app:
	@echo ">>> building ..."
	rm -rf build dist
	arch -i386 python ~/Downloads/pyinstaller-2.0/pyinstaller.py app.spec
	cp dist/* ~/ServicesBox.app/Contents/Resources
	@echo ">>> \033[01;32mdone.\033[00m"

clean:
	rm -f warn*.txt
	rm -f logdict*.log
