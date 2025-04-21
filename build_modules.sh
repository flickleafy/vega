#!/bin/bash

# Check if the 'modules' directory exists
if [ -d "./modules" ]; then
  # Create 'package_modules' directory if it doesn't exist
  mkdir -p ./package_modules

  # Loop through all folders in 'modules'
  for dir in ./modules/*/; do
    # Go into each directory
    cd "$dir" || exit

    # Run Python packaging commands
    python setup.py sdist bdist_wheel

    # Copy wheel files to 'package_modules'
    cp ./dist/*.whl ../../package_modules/

    # Go back to the original directory
    cd - || exit
  done
else
  echo "'modules' directory not found!"
fi

# Check if the 'package_modules' directory exists
if [ -d "./package_modules" ]; then
  # Loop each whl file in 'package_modules'
  for file in ./package_modules/*.whl; do 
    echo "Installing $file..."
    # Install whl file
    pip install "$file" --force-reinstall || {
      echo "Failed to install $file"
      exit 1
    }
  done
else
  echo "'package_modules' directory not found!"
fi