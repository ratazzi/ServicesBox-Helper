#!/bin/bash

# This file only run with Xcode build phase

PATH="$PATH:/usr/local/bin:/opt/local/bin"
PYTHON="$PROJECT_DIR/.runtime/bin/python"
DASHBOARD_DIR="$PROJECT_DIR/dashboard"
PYINSTALLER_DIR="$PROJECT_DIR/pyinstaller"
RESOURCES_DIR="$TARGET_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH"

LASTMODIFIED="$DASHBOARD_DIR/lastmodified"
HEADS="$DASHBOARD_DIR/.git/refs/heads/master"

build_helper() {
    lessc "$DASHBOARD_DIR/resources/static/style.less" "$DASHBOARD_DIR/resources/static/style.css"
    lessc "$DASHBOARD_DIR/resources/static/options.less" "$DASHBOARD_DIR/resources/static/options.css"
    arch -i386 $PYTHON "$PYINSTALLER_DIR/pyinstaller.py" "$DASHBOARD_DIR/app.spec"
    arch -i386 $PYTHON "$PYINSTALLER_DIR/pyinstaller.py" "$DASHBOARD_DIR/ctl.spec"
}

echo ">>> building ..."

touch "$LASTMODIFIED"

if [ `cat $LASTMODIFIED` != `cat $HEADS` ]; then
    build_helper
elif [ ! -e "$DASHBOARD_DIR/dist/ctl" ] || [ ! -e "$DASHBOARD_DIR/dist/dashboard" ]; then
    build_helper
fi

cp "$DASHBOARD_DIR/dist/ctl" "$RESOURCES_DIR/$PRODUCT_NAME.ctl"
cp "$DASHBOARD_DIR/dist/dashboard" "$RESOURCES_DIR/$PRODUCT_NAME.helper"
cat "$HEADS" > "$LASTMODIFIED"
